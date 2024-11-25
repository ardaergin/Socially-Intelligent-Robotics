# main.py

import threading
from sic_framework.devices import Nao
from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
    WhisperConf,
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest
from sic_framework.services.face_detection.face_detection import FaceDetection
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf

from config import OPENAI_KEY, NAO_IP, NUM_TURNS, CAMERA_CONF
from callbacks import on_image, on_faces, touch_stop, imgs_buffer, faces_buffer, interrupted
from nao_control import set_eye_color
from conversation import start_conversation

def main():
    # Initialize devices and services
    desktop_camera_conf = DesktopCameraConf(**CAMERA_CONF)
    desktop = Desktop(camera_conf=desktop_camera_conf)
    face_rec = FaceDetection()
    whisper_conf = WhisperConf(openai_key=OPENAI_KEY)
    whisper = SICWhisper(conf=whisper_conf)
    gpt_conf = GPTConf(openai_key=OPENAI_KEY)
    gpt = GPT(conf=gpt_conf)
    nao = Nao(ip=NAO_IP)

    # Connect services
    try:
        face_rec.connect(desktop.camera)
        whisper.connect(desktop.mic)
        print("Services connected successfully.")
    except Exception as e:
        print(f"Error connecting services: {e}")

    # Register callbacks
    desktop.camera.register_callback(on_image)
    face_rec.register_callback(on_faces)
    nao.buttons.register_callback(lambda event: touch_stop(event, nao))

    # Start the conversation
    interrupted_flag = [interrupted]  # Using list to pass by reference
    start_conversation(nao, whisper, gpt, NUM_TURNS, interrupted_flag)

if __name__ == "__main__":
    main()
