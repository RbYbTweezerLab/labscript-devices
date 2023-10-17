#####################################################################
#                                                                   #
# /labscript_devices/AndorSolis/labscript_devices.py                #
#                                                                   #
# Copyright 2019, Monash University and contributors                #
#                                                                   #
# This file is part of labscript_devices, in the labscript suite    #
# (see http://labscriptsuite.org), and is licensed under the        #
# Simplified BSD License. See the license.txt file in the root of   #
# the project for the full license.                                 #
#                                                                   #
#####################################################################
from labscript_devices.IMAQdxCamera.labscript_devices import IMAQdxCamera

class AndorSolis(IMAQdxCamera):
    description = "Andor scientific camera"
    
    def expose(self, t, name, frametype='frame', trigger_duration=None, action=None):
        """Request an exposure at the given time. A trigger will be produced by the
        parent trigger object, with duration trigger_duration, or if not specified, of
        self.trigger_duration. The frame should have a `name, and optionally a
        `frametype`, both strings. These determine where the image will be stored in the
        hdf5 file. `name` should be a description of the image being taken, such as
        "insitu_absorption" or "fluorescence" or similar. `frametype` is optional and is
        the type of frame being acquired, for imaging methods that involve multiple
        frames. For example an absorption image of atoms might have three frames:
        'probe', 'atoms' and 'background'. For this one might call expose three times
        with the same name, but three different frametypes.
        """
        # Backward compatibility with code that calls expose with name as the first
        # argument and t as the second argument:
        if isinstance(t, str) and isinstance(name, (int, float)):
            msg = """expose() takes `t` as the first argument and `name` as the second
                argument, but was called with a string as the first argument and a
                number as the second. Swapping arguments for compatibility, but you are
                advised to modify your code to the correct argument order."""
            print(dedent(msg), file=sys.stderr)
            t, name = name, t
        if trigger_duration is None:
            trigger_duration = self.trigger_duration
        if trigger_duration is None:
            msg = """%s %s has not had an trigger_duration set as an instantiation
                argument, and none was specified for this exposure"""
            raise ValueError(dedent(msg) % (self.description, self.name))
        if not trigger_duration > 0:
            msg = "trigger_duration must be > 0, not %s" % str(trigger_duration)
            raise ValueError(msg)
        self.trigger(t, trigger_duration)
        self.exposures.append((t, name, frametype, trigger_duration, action))
        return trigger_duration