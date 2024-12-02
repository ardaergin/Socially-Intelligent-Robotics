from sic_framework.devices.desktop import Desktop
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf

class Camera:
    def __init__(self, fx=1.0, fy=1.0, flip=1):
        self.camera = Desktop(camera_conf=DesktopCameraConf(fx=fx, fy=fy, flip=flip))
    
    def register_callback(self, callback):
        self.camera.register_callback(callback)
    
    def get_camera(self):
        return self.camera
