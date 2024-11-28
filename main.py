from sic_framework.devices import Nao
from perception.camera import Camera
from perception.face_detection import FaceDetectionService
from interaction.begin import detect_face_and_welcome
from interaction.conversation import Conversation
from interaction.chat_gpt import GPT
from interaction.speech_to_text import SpeechToText
from control.motion import Motion
from control.leds import LEDControl
from utils.callbacks import on_faces, on_image
import os
import queue

# Loading OPENAI key and NAO IP
from dotenv import load_dotenv
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
NAO_IP = os.getenv("NAO_IP")
if not OPENAI_KEY or not NAO_IP:
    raise EnvironmentError("Missing required environment variables in the .env file.")

# Initialize components
nao = Nao(ip=NAO_IP)
camera = Camera()
face_rec = FaceDetectionService()
whisper = SpeechToText(OPENAI_KEY)
gpt = GPT(OPENAI_KEY)
motion = Motion(nao)
led_control = LEDControl(nao)

# Buffers for image and face detection callbacks
imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)

# Register image and face detection callbacks
camera.register_callback(lambda img: imgs_buffer.put(img))
face_rec.register_callback(lambda faces: faces_buffer.put(faces))

# Connect face detection to the camera
face_rec.connect(camera.get_camera())

# Start the system
if __name__ == "__main__":
    # Wait for face detection and greet the user
    detect_face_and_welcome(nao, led_control, faces_buffer)

    # Initiate the conversation system
    conv = Conversation(nao, whisper, gpt, motion, led_control)
    conv.run_conversation()
