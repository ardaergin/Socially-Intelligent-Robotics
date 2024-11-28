from sic_framework.devices import Nao
from perception.camera import Camera
from perception.face_detection import FaceDetectionService
from interaction.begin import detect_face_and_welcome
from interaction.conversation import Conversation
from interaction.speech_to_text import SpeechToText
from control.motion import Motion
from control.leds import LEDControl
import os
import queue

# Load environment variables
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
NAO_IP = os.getenv("NAO_IP")

if not OPENAI_KEY or not NAO_IP:
    raise EnvironmentError("Missing environment variables in .env file.")

# Initialize NAO and control components
nao = Nao(ip=NAO_IP)
motion = Motion(nao)
led_control = LEDControl(nao)

# Initialize the camera and face detection service
camera = Camera()
face_rec = FaceDetectionService()

# Buffers for image and face detection callbacks
imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)

# Register callbacks for camera and face detection
camera.register_callback(lambda img: imgs_buffer.put(img))
face_rec.register_callback(lambda faces: faces_buffer.put(faces))

# Connect face detection to the camera
face_rec.connect(camera.get_camera())

# Initialize speech-to-text and GPT for conversation
whisper = SpeechToText(OPENAI_KEY)

# Start the system
if __name__ == "__main__":
    try:
        # Wait for face detection and greet the user
        detect_face_and_welcome(nao, led_control, faces_buffer)

        # Initialize and start the conversation system
        conversation = Conversation(nao, whisper_key=OPENAI_KEY, gpt_key=OPENAI_KEY, motion=motion, leds=led_control)
        conversation.run_conversation()
    except KeyboardInterrupt:
        print("System interrupted by user.")
    finally:
        print("Shutting down the system. Turning off LEDs.")
        led_control.set_eye_color("off")
