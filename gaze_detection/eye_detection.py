from pathlib import Path

import cv2
import numpy as np
from numpy import array

from sic_framework.core import sic_logging
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import (
    BoundingBox,
    BoundingBoxesMessage,
    CompressedImageMessage,
    CompressedImageRequest,
    SICConfMessage,
    SICMessage,
)
from sic_framework.core.service_python2 import SICService


class EyeDetectionConf(SICConfMessage):
    def __init__(self, minW=30, minH=30):
        """
        :param minW       Minimum possible eye width in pixels
        :param minH       Minimum possible eye height in pixels
        """
        SICConfMessage.__init__(self)

        # Define min window size to be recognized as an eye
        self.minW = minW
        self.minH = minH


class EyeDetectionComponent(SICComponent):
    def __init__(self, *args, **kwargs):
        super(EyeDetectionComponent, self).__init__(*args, **kwargs)
        script_dir = Path(__file__).parent.resolve()
        cascadePath = str(script_dir / "haarcascade_eye.xml")
        self.eyeCascade = cv2.CascadeClassifier(cascadePath)

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage, CompressedImageRequest]

    @staticmethod
    def get_conf():
        return EyeDetectionConf()

    @staticmethod
    def get_output():
        return BoundingBoxesMessage

    def on_message(self, message):
        bboxes = self.detect(message.image)
        self.output_message(bboxes)

    def on_request(self, request):
        return self.detect(request.image)

    def detect(self, image):
        img = array(image).astype(np.uint8)

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        eyes = self.eyeCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(int(self.params.minW), int(self.params.minH)),
        )

        eyes = [BoundingBox(x, y, w, h) for (x, y, w, h) in eyes]

        return BoundingBoxesMessage(eyes)

    def are_eyes_on_image(self, image):
        img = array(image).astype(np.uint8)

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        eyes = self.eyeCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(int(self.params.minW), int(self.params.minH)),
        )

        eyes = [BoundingBox(x, y, w, h) for (x, y, w, h) in eyes]

        return len(eyes) >= 2


class EyeDetection(SICConnector):
    component_class = EyeDetectionComponent


def main():
    SICComponentManager([EyeDetectionComponent])


if __name__ == "__main__":
    main()
