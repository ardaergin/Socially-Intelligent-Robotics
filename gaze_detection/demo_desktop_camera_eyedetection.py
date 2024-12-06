import queue
import cv2
from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.face_detection.face_detection import FaceDetection
from custom_components.eye_detection import EyeDetection

""" 
This demo recognizes faces from your webcam and displays the result on your laptop.

IMPORTANT
face-detection service needs to be running:
1. run-face-detection

eye-detection service also needs to be running:
2. python3 custom_components/eye_detection.py

To run this file:
PYTHONPATH=. python3 demos/desktop/demo_desktop_camera_eyedetection.py
Without the python path specification, it will raise a ModuleNotFound exception.
"""

imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)
eyes_buffer = queue.Queue(maxsize=1)


def on_image(image_message: CompressedImageMessage):
    imgs_buffer.put(image_message.image)

def on_faces(message: BoundingBoxesMessage):
    faces_buffer.put(message.bboxes)

# I don't understand how exactly this is supposed to work:
def on_eyes(message:BoundingBoxesMessage):
    eyes_buffer.put(message.bboxes)

# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)

# Connect to the services
desktop = Desktop(camera_conf=conf)

face_rec = FaceDetection()
eye_rec = EyeDetection()
# CUSTOM FACE DETECTION EXAMPLE
# face_rec = CustomFaceDetection()

# Feed the camera images into the face recognition component
face_rec.connect(desktop.camera)
eye_rec.connect(desktop.camera)
# Send back the outputs to this program
desktop.camera.register_callback(on_image)
face_rec.register_callback(on_faces)
eye_rec.register_callback(on_eyes)

"""
for face in faces:
    utils_cv2.draw_bbox_on_image(face, img, color=(0, 0, 255))

for eye in eyes:
    utils_cv2.draw_bbox_on_image(eye, img, color=(0, 128, 255))
"""

while True:
    face_eyes = []

    img = imgs_buffer.get()
    faces = faces_buffer.get()

    #face_bboxes_message = BoundingBoxesMessage(faces)

    # Send face bounding boxes to FaceEyeDetection
    #eye_rec.send_message(face_bboxes_message)

    # Retrieve detected eyes
    eyes = eyes_buffer.get()

    for face in faces:
        #utils_cv2.draw_bbox_on_image(face, img, color=(0, 0, 255))

        # Extract face bounding box
        face_x, face_y, face_w, face_h = face.x, face.y, face.w, face.h

        for eye in eyes:
            # Extract eye bounding box
            eye_x, eye_y, eye_w, eye_h = eye.x, eye.y, eye.w, eye.h

            # Check if the eye is within the face boundaries
            if (
                    face_x <= eye_x <= face_x + face_w
                    and face_y <= eye_y <= face_y + face_h
                    and face_x <= eye_x + eye_w <= face_x + face_w
                    and face_y <= eye_y + eye_h <= face_y + face_h
            ):
                # Eye is inside the face; draw the eye bounding box
                #utils_cv2.draw_bbox_on_image(eye, img, color=(0, 128, 255))  # Orange for eyes
                face_eyes.append(eye)


    print(f"I see {len(face_eyes)} eyes!")
    #cv2.imshow("", img)
    #cv2.waitKey(1)

