from sic_framework.devices import Nao
from perception.camera import Camera
from perception.face_detection import FaceDetectionService
from interaction.conversation import Conversation
from interaction.interruption import Interruption
from interaction.chat_gpt import ChatGPT
from interaction.speech_to_text import SpeechToText
from control.motion import Motion
from control.leds import LEDControl
from utils.callbacks import on_faces, on_image
import os

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
gpt = ChatGPT(OPENAI_KEY)
motion = Motion(nao)
led_control = LEDControl(nao)

# Connect devices and services
face_rec.connect(camera.get_camera())
camera.register_callback(on_image)
face_rec.register_callback(on_faces)

# Start the system
conv = Conversation(nao, whisper, gpt, motion, led_control)
interrupt = Interruption(nao, conv)

conv.start()
