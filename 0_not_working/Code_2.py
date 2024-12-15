import os
import time
import queue
import random
import threading
import cv2
from sic_framework.devices import Nao
from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
    WhisperConf,
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest, OpenAI
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)
from sic_framework.services.face_detection.face_detection import FaceDetection
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest

# Environment Variables
from dotenv import load_dotenv

load_dotenv()
openai_key = os.getenv("OPENAI_KEY")
nao_ip = os.getenv("NAO_IP")

if not openai_key or not nao_ip:
    raise EnvironmentError("Missing environment variables in .env file.")

nao = Nao(ip=nao_ip)

nao.motion.request(NaoPostureRequest("Stand", 0.5))

# Initialize buffers for images and face detection
imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)


# Callback functions for receiving image and face detection data
def on_image(image_message: CompressedImageMessage):
    imgs_buffer.put(image_message.image)


def on_faces(message: BoundingBoxesMessage):
    faces_buffer.put(message.bboxes)


# Configuration for the desktop camera
camera_conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)

# Initialize devices and services
desktop = Desktop(camera_conf=camera_conf)
face_rec = FaceDetection()
whisper_conf = WhisperConf(openai_key=openai_key)
whisper = SICWhisper(conf=whisper_conf)
gpt_conf = GPTConf(openai_key=openai_key, model="gpt-4o-mini")
gpt = GPT(conf=gpt_conf)
client = OpenAI(api_key=openai_key)

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


# Function to change NAO's eye color
def set_eye_color(color):
    if color == 'green':
        nao.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 1, 0, 0))
    elif color == 'blue':
        nao.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 0, 1, 0))
    elif color == 'off':
        nao.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 0, 0, 0))


# Function to play animations while NAO is speaking
def play_random_animations(stop_event):
    while not stop_event.is_set():
        animation_number = random.randint(1, 11)
        animation_path = f"animations/Stand/Gestures/Explain_{animation_number}"
        nao.motion.request(NaoqiAnimationRequest(animation_path))
        # time.sleep(random.uniform(1, 2))  # Wait a bit before playing another animation
        time.sleep(random.random())


# Function to send sentence to NAO's TTS and play animations concurrently
def send_sentence_and_animation_to_nao(sentence):
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=play_random_animations, args=(stop_event))

    try:
        animation_thread.start()

        # Send the TTS request
        response = nao.tts.request(NaoqiTextToSpeechRequest(sentence))
        print(f"NAO says: {sentence}")

        # Simulate waiting for TTS completion
        # Replace the "completed" attribute with a dummy wait
        # time.sleep(len(sentence) / 5)  # Estimate based on speaking speed (~5 chars/sec)

        stop_event.set()
        animation_thread.join()
    except Exception as e:
        print(f"Error sending sentence to NAO: {e}")
    finally:
        stop_event.set()
        if animation_thread.is_alive():
            animation_thread.join()


from nltk.tokenize import sent_tokenize
import nltk

nltk.download('punkt_tab')


def break_into_sentences(text):
    return sent_tokenize(text)


conversation = [{"role": "system",
                 "content": "You are a social robot carrying out an experiment. You will only talk to one user at a time. The scenario is that you are a time traveler that has been to every time period since the era of dinosaurs. Talk with an adventurous tone and use real facts of that time period to tell a story in that time period. Always remain on the topic unless you are asked to change it. Don't talk about sensitive or private information about the user. First ask the user's name and then start off with introducing a random time period followed by telling a story from that time period."}]


def converse(user_input):
    conversation.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation,
    )
    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})

    return reply


def touch_stop(event):
    global interrupted
    sensor = event.value
    print(f"sensor info 0: {sensor[0]}")
    print(f"sensor info 1: {sensor[1]}")
    print(event.value)

    # Detect if ANY touch sensor is activated
    # We should change this to only head or something
    touch_detection = any(sensor_info[1] for sensor_info in sensor)

    if touch_detection:
        print("Touch detected! Stopping current speech and setting interruption flag.")
        # Stop the current speech
        # nao.tts.stop()
        # Set the interruption flag
        interrupted = True


nao.buttons.register_callback(touch_stop)

# historical_roles.py
import os
import json
import random


class HistoricalRoles:
    def __init__(self):
        """
        Initialize the HistoricalRoles class.

        :param roles_file: Path to the JSON file containing historical roles.
        """
        self.roles = self._load_roles("data/amsterdam_eras.json")

    def _load_roles(self):
        """
        Load historical roles from a JSON file.

        :param roles_file: Path to the JSON file containing historical roles.
        :return: Dictionary of roles by era.
        """
        roles_path = os.path.join(os.path.dirname(__file__), "../data", "amsterdam_eras.json")
        # roles_path = "./data/amsterdam_eras.json"
        try:
            with open(roles_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Roles file {roles_path} not found.")
            return {}

    def get_random_role(self):
        """
        Get a random historical role from the available eras.

        :return: A dictionary containing role, era description, interactive questions, and dialogue style.
        """
        if not self.roles:
            return None
        era = random.choice(list(self.roles.keys()))
        return self.roles[era]

    def format_as_prompt(self, role_data):
        """
        Format the role data into a ChatGPT-compatible system prompt.

        :param role_data: A dictionary containing role, era description, questions, and dialogue style.
        :return: A string system prompt for ChatGPT.
        """
        if not role_data:
            return "You are a historian in Amsterdam. Engage with the user using your knowledge of Amsterdam's history."

        return (
            f"You are role-playing as:\n"
            f"{role_data['role']}\n\n"
            f"Era Description:\n{role_data['era_description']}\n\n"
            f"Interactive Questions to guide the conversation:\n"
            f"{' '.join(role_data['interactive_questions'])}\n\n"
            f"Dialogue Style:\n"
            f"{' '.join(role_data['dialogue_style'])}\n\n"
            f"Stay in character and engage the user interactively."
        )






# Main conversation manager class
class ConversationManager:
    def __init__(self, nao, whisper, gpt_client, historical_roles):
        self.nao = nao
        self.whisper = whisper
        self.gpt_client = gpt_client
        self.historical_roles = historical_roles
        self.interrupted = False
        self.current_role = None
        self.conversation = [
            {"role": "system",
             "content": "You are a social robot carrying out an experiment. You will only talk to one user at a time. "
                        "The scenario is that you are a time traveler that has been to every time period since the era of dinosaurs. "
                        "Talk with an adventurous tone and use real facts of that time period to tell a story in that time period. "
                        "Always remain on the topic unless you are asked to change it. First ask the user's name and then start off "
                        "with introducing a random time period followed by telling a story from that time period."}
        ]
        self.user_responses = []  # To store the last 3 user responses

    def initialize_conversation(self):
        """Fetches and sets the initial historical role."""
        self.current_role = self.historical_roles.get_random_role()
        intro_message = self.historical_roles.format_as_prompt(self.current_role)
        self.send_to_nao(intro_message)

    def process_user_input(self, user_input):
        """Processes the user's input and generates a response."""
        self.conversation.append({"role": "user", "content": user_input})
        response = self.gpt_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.conversation,
        )
        reply = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": reply})
        return reply

    def send_to_nao(self, text):
        """Sends a message to NAO and plays animations concurrently."""
        send_sentence_and_animation_to_nao(text)

    def handle_short_response(self, user_input):
        """Handles short responses by switching to a new role if needed."""
        # Keep track of user responses
        self.user_responses.append(user_input)
        if len(self.user_responses) > 3:
            self.user_responses.pop(0)  # Maintain only the last 3 responses

        # Check if the last 3 responses are all short
        if all(len(response.split()) < 5 for response in self.user_responses):
            print("Detected multiple short responses. Switching topic.")
            self.nao.tts.request(
                NaoqiTextToSpeechRequest("I noticed several short responses. Let’s switch to another story!"))
            self.current_role = self.historical_roles.get_random_role()
            intro_message = self.historical_roles.format_as_prompt(self.current_role)
            self.send_to_nao(intro_message)
            self.user_responses.clear()  # Reset after switching topic

    def handle_interruption(self):
        """Handles user interruptions."""
        self.nao.tts.request(NaoqiTextToSpeechRequest("Oh, I understand. Let me switch topics."))
        self.current_role = self.historical_roles.get_random_role()
        intro_message = self.historical_roles.format_as_prompt(self.current_role)
        self.send_to_nao(intro_message)
        self.interrupted = False

    def interact(self, num_turns=10):
        """Main interaction loop."""
        for _ in range(num_turns):
            try:
                print("Talk now!")
                set_eye_color('green')  # Indicate NAO is listening
                transcript = self.whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
                user_input = transcript.transcript
                print("User:", user_input)

                # Handle short responses
                if len(user_input.split()) < 5:
                    self.handle_short_response(user_input)
                    continue

                set_eye_color('blue')  # Indicate NAO is processing
                response = self.process_user_input(user_input)
                print("ChatGPT Response:", response)

                # Send response to NAO
                for sentence in break_into_sentences(response):
                    self.send_to_nao(sentence)
                    if self.interrupted:
                        self.handle_interruption()
                        break
            except Exception as e:
                print(f"Error during interaction: {e}")




# Initialize the conversation manager
historical_roles = HistoricalRoles()
conversation_manager = ConversationManager(nao, whisper, client, historical_roles)

# Main loop to detect faces and start conversation
print("Waiting for a face to start the conversation...")
face_detected = False

while not face_detected:
    try:
        img = imgs_buffer.get(timeout=5)
        faces = faces_buffer.get(timeout=5)

        if faces:
            print("Face detected! Starting conversation...")
            face_detected = True
            welcome_message = (
                "Hello! I am a social robot, and today, we will time-travel together to explore the fascinating history of Amsterdam. Get ready for an immersive experience! What's your name?")
            send_sentence_and_animation_to_nao(welcome_message)
            conversation_manager.initialize_conversation()
            conversation_manager.interact(num_turns=10)
    except queue.Empty:
        print("No face detected yet, still waiting...")
    except Exception as e:
        print(f"Error during face detection: {e}")

print("Conversation done!")
nao.motion.request(NaoPostureRequest("Sit", 0.5))
set_eye_color('off')  # Optionally turn off the LEDs after the conversation

