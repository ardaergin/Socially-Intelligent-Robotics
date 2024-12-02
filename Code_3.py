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
        time.sleep(len(sentence) / 5)  # Estimate based on speaking speed (~5 chars/sec)

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





conversation = [{"role": "system", "content": "You are a social robot carrying out an experiment. You will only talk to one user at a time. The scenario is that you are a time traveler that has been to every time period since the era of dinosaurs. Talk with an adventurous tone and use real facts of that time period to tell a story in that time period. Always remain on the topic unless you are asked to change it. Don't talk about sensitive or private information about the user. First ask the user's name and then start off with introducing a random time period followed by telling a story from that time period."}]
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







# Main loop to detect faces and initiate conversation
print("Waiting for a face to start the conversation...")

face_detected = False

while not face_detected:
    try:
        img = imgs_buffer.get(timeout=5)
        faces = faces_buffer.get(timeout=5)

        if faces:
            print("Face detected! Starting conversation...")
            face_detected = True
            welcome_message = ("Hello! I am a social robot, and today, we will time-travel together to explore the fascinating history of Amsterdam. Get ready for an immersive experience!")
            send_sentence_and_animation_to_nao(welcome_message)
            set_eye_color('green')  # NAO eyes turn green to indicate listening
    except queue.Empty:
        print("No face detected yet, still waiting...")
    except Exception as e:
        print(f"Error during face detection: {e}")





# Start the conversation loop
NUM_TURNS = 10

i = 0
while i < NUM_TURNS:
    print("Talk now!")
    try:
        # Ensure listening only starts after NAO finishes speaking
        set_eye_color('green')  # Indicate NAO is listening
        transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
        inp = transcript.transcript
        print("Transcript:", inp)

        # Change NAO's eye color to blue while talking
        set_eye_color('blue')
        # reply = gpt.request(GPTRequest(inp))
        # response = reply.response
        reply = converse(inp)
        print("ChatGPT Response:", reply)

        # Send ChatGPT's response to NAO's TTS and wait until it finishes, playing animations
        gpt_response_in_sentences = break_into_sentences(reply)
        
        for sentence in gpt_response_in_sentences:
            send_sentence_and_animation_to_nao(nao, sentence)
            if interrupted:
                print("Interruption detected. Responding to touch.")
                # Respond with the touch message
                nao.tts.request(NaoqiTextToSpeechRequest("Oh, I understand that you are uninterested in this subject, let me switch."))
                break

        # Only start listening again after speech completes
        set_eye_color(nao, 'green')

        if interrupted:
            reply = gpt.request(GPTRequest("Can you tell a story about the roman empire?"))
            response = reply.response
            gpt_response_in_sentences = break_into_sentences(response)
            print("ChatGPT Response:", response)
            interrupted = False


        # Send ChatGPT's response to NAO's TTS and wait until it finishes, playing animations
        send_sentence_and_animation_to_nao(reply)

        # Only start listening again after speech completes
        set_eye_color('green')
    except Exception as e:
        print(f"An error occurred during the conversation: {e}")

    i += 1

print("Conversation done!")
nao.motion.request(NaoPostureRequest("Sit", 0.5))
set_eye_color('off')  # Optionally turn off the LEDs after the conversation





























# historical_roles.py
import os
import json
import random

class HistoricalRoles:
    def __init__(self, roles_file="data/amsterdam_eras.json"):
        """
        Initialize the HistoricalRoles class.

        :param roles_file: Path to the JSON file containing historical roles.
        """
        self.roles = self._load_roles(roles_file)

    def _load_roles(self, roles_file):
        """
        Load historical roles from a JSON file.

        :param roles_file: Path to the JSON file containing historical roles.
        :return: Dictionary of roles by era.
        """
        roles_path = os.path.join(os.path.dirname(__file__), "..", roles_file)
        try:
            with open(roles_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Roles file '{roles_file}' not found.")
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




# immersive/images.py
import cv2
import time

def display_images_sequentially(images, duration=5, transition_time=1):
    """
    Display a sequence of images in the same window with a smooth transition.

    :param images: List of image paths to display.
    :param duration: Duration in seconds to display each image.
    :param transition_time: Duration in seconds for the transition effect.
    """
    try:
        cv2.namedWindow("Historical Image", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Historical Image", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        previous_img = None

        for idx, image_path in enumerate(images):
            img = cv2.imread(image_path)
            if img is None:
                print(f"Image not found: {image_path}")
                continue

            if previous_img is not None:
                fade_transition(previous_img, img, transition_time)

            cv2.imshow("Historical Image", img)
            cv2.waitKey(duration * 1000)
            previous_img = img

        cv2.destroyAllWindows()
    except Exception as e:
        print(f"Error displaying images: {e}")

def fade_transition(image1, image2, transition_time):
    try:
        steps = int(transition_time * 30)
        for alpha in range(steps + 1):
            blend = cv2.addWeighted(image1, 1 - alpha / steps, image2, alpha / steps, 0)
            cv2.imshow("Historical Image", blend)
            cv2.waitKey(int(1000 / 30))
    except Exception as e:
        print(f"Error during transition: {e}")

# immersive/sound.py
import pygame
import time

def play_audio_loop(audio_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play(-1)
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        pygame.mixer.quit()

def stop_audio():
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"Error stopping audio: {e}")



# Updated ConversationManager
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
        self.user_responses = []
        self.media_thread = None
        self.audio_thread = None

    def initialize_conversation(self):
        self.switch_topic()

    def process_user_input(self, user_input):
        self.conversation.append({"role": "user", "content": user_input})
        response = self.gpt_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.conversation,
        )
        reply = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": reply})
        return reply

    def send_to_nao(self, text):
        send_sentence_and_animation_to_nao(text)

    def handle_short_response(self, user_input):
        self.user_responses.append(user_input)
        if len(self.user_responses) > 3:
            self.user_responses.pop(0)

        if all(len(response.split()) < 5 for response in self.user_responses):
            print("Detected multiple short responses. Switching topic.")
            self.switch_topic()
            self.user_responses.clear()

    def handle_interruption(self):
        print("Interruption detected. Switching topic.")
        self.switch_topic()
        self.interrupted = False

    def switch_topic(self):
        self.stop_media_threads()
        self.current_role = self.historical_roles.get_random_role()
        if not self.current_role:
            self.send_to_nao("I couldn't find any historical role. Let's continue!")
            return
        intro_message = self.historical_roles.format_as_prompt(self.current_role)
        self.send_to_nao(intro_message)
        self.start_media_threads(self.current_role)

    def start_media_threads(self, role_data):
        self.stop_media_threads()

        if "image" in role_data and isinstance(role_data["image"], list):
            self.media_thread = threading.Thread(
                target=display_images_sequentially, args=(role_data["image"],)
            )
            self.media_thread.start()

        if "audio" in role_data and role_data["audio"]:
            self.audio_thread = threading.Thread(
                target=play_audio_loop, args=(role_data["audio"],)
            )
            self.audio_thread.start()

    def stop_media_threads(self):
        stop_audio()
        if self.media_thread and self.media_thread.is_alive():
            self.media_thread.join()
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()

    def interact(self, num_turns=10):
        for _ in range(num_turns):
            try:
                set_eye_color('green')
                transcript = self.whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
                user_input = transcript.transcript
                print("User:", user_input)

                if len(user_input.split()) < 5:
                    self.handle_short_response(user_input)
                    continue

                set_eye_color('blue')
                response = self.process_user_input(user_input)
                print("ChatGPT Response:", response)

                for sentence in break_into_sentences(response):
                    self.send_to_nao(sentence)
                    if self.interrupted:
                        self.handle_interruption()
                        break
            except Exception as e:
                print(f"Error during interaction: {e}")

# Main loop
historical_roles = HistoricalRoles()
conversation_manager = ConversationManager(nao, whisper, client, historical_roles)

print("Waiting for a face to start the conversation...")
face_detected = False

while not face_detected:
    try:
        img = imgs_buffer.get(timeout=5)
        faces = faces_buffer.get(timeout=5)

        if faces:
            print("Face detected! Starting conversation...")
            face_detected = True
            welcome_message = "Hello! I am a social robot, and today, we will time-travel together to explore the fascinating history of Amsterdam. Get ready for an immersive experience!"
            send_sentence_and_animation_to_nao(welcome_message)
            conversation_manager.initialize_conversation()
            conversation_manager.interact(num_turns=10)
    except queue.Empty:
        print("No face detected yet, still waiting...")
    except Exception as e:
        print(f"Error during face detection: {e}")

print("Conversation done!")
nao.motion.request(NaoPostureRequest("Sit", 0.5))
set_eye_color('off')
