# callbacks.py: Handles image and face detection callbacks.
import queue
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)

# Initialize buffers for images and face detection
imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)


def on_image(image_message: CompressedImageMessage):
    imgs_buffer.put(image_message.image)

def on_faces(message: BoundingBoxesMessage):
    faces_buffer.put(message.bboxes)