from sic_framework.services.face_detection.face_detection import FaceDetection

class FaceDetectionService:
    def __init__(self):
        self.face_detection = FaceDetection()
    
    def connect(self, camera):
        self.face_detection.connect(camera)
    
    def register_callback(self, callback):
        self.face_detection.register_callback(callback)
