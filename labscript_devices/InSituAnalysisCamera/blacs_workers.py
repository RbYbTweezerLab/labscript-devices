


class InSituAnalysisCameraWorker(IMAQdxCameraWorker):

    interface_class = IMAQdx_Camera

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