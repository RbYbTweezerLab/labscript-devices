#####################################################################
#                                                                   #
# /labscript_devices/AndorSolis/blacs_workers.py                    #
#                                                                   #
# Copyright 2019, Monash University and contributors                #
#                                                                   #
# This file is part of labscript_devices, in the labscript suite    #
# (see http://labscriptsuite.org), and is licensed under the        #
# Simplified BSD License. See the license.txt file in the root of   #
# the project for the full license.                                 #
#                                                                   #
#####################################################################
from zprocess import rich_print
import threading
from labscript_devices.IMAQdxCamera.blacs_workers import MockCamera, IMAQdxCameraWorker

class AndorCamera(object):

    def __init__(self):
        global AndorCam
        from .andor_sdk.andor_utils import AndorCam
        self.camera = AndorCam()
        self.attributes = self.camera.default_acquisition_attrs
        self.exception_on_failed_shot = True

    def set_attributes(self, attr_dict):
        self.attributes.update(attr_dict)
        
    def set_attribute(self, name, value):
        self.attributes[name] = value

    def get_attribute_names(self, visibility_level, writeable_only=True):
        return list(self.attributes.keys())

    def get_attribute(self, name):
        return self.attributes[name]

    def snap(self):
        """Acquire a single image and return it"""
        self.configure_acquisition()
        self.camera.acquire()
        images = self.camera.download_acquisition()
        print(f'Exposure time was {self.camera.exposure_time}')
        return images # This may be a 3D array of several images

    def configure_acquisition(self, continuous=False, bufferCount=None):
        self.camera.setup_acquisition(self.attributes)

    def grab(self):
        """ Grab last/single image """
        img = self.snap()
        # Consider using run til abort acquisition mode...
        return img

    def grab_multiple(self, n_images, images, waitForNextBuffer=True, actions=None):
        """Grab n_images into images array during buffered acquistion."""
    
        # TODO: Catch timeout errors, check if abort, else keep trying.
        if actions == None:
            actions = n_images*[None]
        print(f"Camera configured in {self.camera.acquisition_mode} mode.")
        print(f"Actual readout time is {self.camera.readout_time} s.")
        print(f"Keep clean cycle time is {self.camera.keepClean_time} s.")
        if 'kinetic_series' in self.camera.acquisition_mode: 
            print(f"Kinetics number is {self.camera.default_acquisition_attrs['number_kinetics']}.")
            print(f"Actual kinetics period is {self.camera.kinetics_timing} s.")
        print(f"Actual exposure time is {self.camera.exposure_time} s.")
        print(f"Actual digitization speed (HSpeed) is {self.camera.horizontal_shift_speed} MHz.")
        print(f"Actual vertical shift speed is {self.camera.vs_speed} us.")
        rich_print(f" ---> EMCCD Gain value is {self.camera.emccd_gain}.", color='magenta')
        if 'fast_kinetics' in self.camera.acquisition_mode:
            print(f"FK mode Kinetics Number is {self.camera.number_fast_kinetics}.")
        print(f"    ---> Attempting to grab {n_images} acquisition(s).")

        if 'single' in self.camera.acquisition_mode:
            for image_number in range(n_images):
                self.camera.acquire()
                print(f"    {image_number}: Acquire complete")
                downloaded = self.camera.download_acquisition()
                print(f"    {image_number}: Download complete")

                if actions[image_number] != None:
                    self.execute_action(actions[image_number], downloaded)
                
                images.append(downloaded)
                self.camera.armed = True
            self.camera.armed = False
            print(f"Got {len(images)} of {n_images} acquisition(s).")
        elif 'fast_kinetics' in self.camera.acquisition_mode:
            nacquisitions = n_images // self.camera.number_fast_kinetics
            for image_number in range(nacquisitions):
                self.camera.acquire()
                print(f"    {image_number}: Acquire complete")
                downloaded = self.camera.download_acquisition()
                print(f"    {image_number}: Download complete")

                if actions[image_number] != None:
                    self.execute_action(actions[image_number], downloaded)

                images.extend(list(downloaded))
                self.camera.armed = True
            self.camera.armed = False # This last disarming may be redundant
            print(f"Got {len(images)} images in {nacquisitions} FK series acquisition(s).")    
        else: 
            self.camera.acquire()
            print(f"    Acquire complete")
            downloaded = self.camera.download_acquisition()
            print(f"    images {len(images)}-{len(images) + len(downloaded)}: Download complete")

            if actions[image_number] != None:
                self.execute_action(actions[image_number], downloaded)
            
            images.extend(list(downloaded))
            self.camera.armed = False
            print(f"Got {len(images)} of {n_images} acquisition(s).")
   

    def stop_acquisition(self):
        pass

    def abort_acquisition(self):
        self.camera.abort_acquisition()
        self._abort_acquisition = True

    def _decode_image_data(self, img):
        pass

    def close(self):
        self.camera.shutdown()
    
    def execute_action(self, action, data):
        # Execute script or exe here:
        print(f"Executing action: {action}")
        try:
            with open(action, 'r') as file:
                python_code = file.read()
                exec(python_code)
        except FileNotFoundError:
            print(f"Error: The file '{action}' does not exist.")

class AndorSolisWorker(IMAQdxCameraWorker):

    interface_class = AndorCamera

    def get_camera(self):
        """ Andor cameras may not be specified by serial numbers"""
        if self.mock:
            return MockCamera()
        else:
            return self.interface_class()
            
    def get_attributes_as_dict(self, visibility_level):
        """Return a dict of the attributes of the camera for the given visibility
        level"""
        return self.camera.attributes

    def transition_to_buffered(self, device_name, h5_filepath, initial_values, fresh):
        if getattr(self, 'is_remote', False):
            h5_filepath = path_to_local(h5_filepath)
        if self.continuous_thread is not None:
            # Pause continuous acquistion during transition_to_buffered:
            self.stop_continuous(pause=True)
        with h5py.File(h5_filepath, 'r') as f:
            group = f['devices'][self.device_name]
            if not 'EXPOSURES' in group:
                return {}
            self.h5_filepath = h5_filepath
            self.exposures = group['EXPOSURES'][:]
            self.n_images = len(self.exposures)
            self.actions = self.exposures[:,4]
            # Get the camera_attributes from the device_properties
            properties = labscript_utils.properties.get(
                f, self.device_name, 'device_properties'
            )
            camera_attributes = properties['camera_attributes']
            self.stop_acquisition_timeout = properties['stop_acquisition_timeout']
            self.exception_on_failed_shot = properties['exception_on_failed_shot']
            saved_attr_level = properties['saved_attribute_visibility_level']
            self.camera.exception_on_failed_shot = self.exception_on_failed_shot
        # Only reprogram attributes that differ from those last programmed in, or all of
        # them if a fresh reprogramming was requested:
        if fresh:
            self.smart_cache = {}
        self.set_attributes_smart(camera_attributes)
        # Get the camera attributes, so that we can save them to the H5 file:
        if saved_attr_level is not None:
            self.attributes_to_save = self.get_attributes_as_dict(saved_attr_level)
        else:
            self.attributes_to_save = None
        print(f"Configuring camera for {self.n_images} images.")
        self.camera.configure_acquisition(continuous=False, bufferCount=self.n_images)
        self.images = []
        self.acquisition_thread = threading.Thread(
            target=self.camera.grab_multiple,
            args=(self.n_images, self.images, self.actions),
            daemon=True,
        )
        self.acquisition_thread.start()
        return {}