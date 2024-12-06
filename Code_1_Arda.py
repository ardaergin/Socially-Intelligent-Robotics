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
    animation_thread = threading.Thread(target=play_random_animations, args=(stop_event,))

    try:
        animation_thread.start()

        # Send the TTS request
        response1 = nao.tts.request(NaoqiTextToSpeechRequest(sentence))
        print(f"NAO says: {sentence}")

        # Simulate waiting for TTS completion
        # Replace the "completed" attribute with a dummy wait
        # time.sleep(len(sentence) / 5)  # Estimate based on speaking speed (~5 chars/sec)
        #while not response1.completed:
        #    time.sleep(0.1)

        stop_event.set()
        animation_thread.join()
    except Exception as e:
        print(f"Error sending sentence to NAO: {e}")
    finally:
        stop_event.set()
        if animation_thread.is_alive():
            animation_thread.join()


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
# nao.buttons.register_callback(touch_stop)





# Face detection
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
                "Hello! I am a social robot, and today, we will time-travel together to explore the fascinating history of Amsterdam.")
            send_sentence_and_animation_to_nao(welcome_message)
            set_eye_color('green')  # NAO eyes turn green to indicate listening
    except queue.Empty:
        print("No face detected yet, still waiting...")
    except Exception as e:
        print(f"Error during face detection: {e}")








from HistoricalRoles import HistoricalRoles
historical_roles = HistoricalRoles()
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt_tab')


def break_into_sentences(text):
    """Split text into sentences using NLTK."""
    return sent_tokenize(text)


# Starting system prompt
CONVERSATION_START_PROMPT = {
    "role": "system",
    "content": (
        "You are a social robot carrying out an experiment. You will only talk to one user at a time. "
        "The scenario is that you are a time traveler who has visited different periods in Amsterdam. "
        "Talk with an adventurous tone and use real facts of that time period to tell a story. "
        "Always remain on topic unless the user requests otherwise. Avoid sensitive or private information. "
        "Ask engaging questions to guide the conversation."
    ),
}

# Initialize conversation
conversation = [CONVERSATION_START_PROMPT]


def add_to_conversation(role, content):
    """Add a message to the conversation log."""
    conversation.append({"role": role, "content": content})


def get_gpt_response(user_input=None, system_input=None):
    """
    Get a response from the GPT model based on user or system input.

    :param user_input: User's input string.
    :param system_input: System's input string (used for prompts like roles).
    :return: GPT response string.
    """
    if user_input:
        add_to_conversation("user", user_input)
    elif system_input:
        add_to_conversation("system", system_input)

    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=conversation
    )
    reply = response.choices[0].message.content
    add_to_conversation("assistant", reply)
    return reply



def listen_for_interrupt(stop_event, interruption_callback):
    """
    Continuously listen for user commands while NAO is speaking.

    :param stop_event: Event to stop the listening loop.
    :param interruption_callback: Function to call if an interrupt keyword is detected.
    """
    while not stop_event.is_set():
        try:
            transcript = whisper.request(GetTranscript(timeout=5, phrase_time_limit=5))
            user_input = transcript.transcript
            print("User Input While Speaking:", user_input)

            if check_for_interrupt_keyword(user_input):
                print("Interrupt command detected!")
                interruption_callback()
                break
        except Exception as e:
            print(f"Error while listening: {e}")



def handle_gpt_response(response):
    """
    Process GPT response by breaking it into sentences and sending them to NAO,
    while also listening for user interruptions.
    """
    sentences = break_into_sentences(response)
    stop_event = threading.Event()
    
    # Define a callback to handle interruption
    def interruption_callback():
        global interrupted
        interrupted = True
        stop_event.set()
        nao.tts.request(NaoqiTextToSpeechRequest("Oh, I understand. Let me switch topics."))

    # Start listening in a separate thread
    listener_thread = threading.Thread(target=listen_for_interrupt, args=(stop_event, interruption_callback))
    listener_thread.start()

    try:
        for sentence in sentences:
            send_sentence_and_animation_to_nao(sentence)
            if interrupted:
                print("Interruption detected. Stopping further responses.")
                break
    finally:
        # Stop the listener thread
        stop_event.set()
        listener_thread.join()



def check_for_interrupt_keyword(user_input, keywords=None):
    """
    Check if the user's input contains any interrupt keyword.

    :param user_input: String input from the user.
    :param keywords: List of keywords to trigger an interruption.
    :return: Boolean indicating whether an interrupt keyword was detected.
    """
    if keywords is None:
        keywords = ["switch", "change", "stop", "please switch"]
    
    # Convert input to lowercase and check for keywords
    return any(keyword in user_input.lower() for keyword in keywords)




def detect_disinterest_via_response_length(user_responses, word_threshold=5, response_count=2):
    """
    Detect user disinterest based on the length of the last few responses.

    :param user_responses: List of recent user responses.
    :param word_threshold: Number of words below which a response is considered short.
    :param response_count: Number of recent responses to analyze.
    :return: Boolean indicating whether the user is disinterested.
    """
    # Keep only the last `response_count` responses
    recent_responses = user_responses[-response_count:]

    # Check if all recent responses are below the word threshold
    return len(recent_responses) == response_count and all(
        len(response.split()) < word_threshold for response in recent_responses
    )




# Initialize variables
NUM_TURNS = 10
FIRST_ERA = "1500s"  # Constant for the initial role
interrupted = False
user_responses = []  # List to store user responses for analyzing disinterest

for turn_index in range(NUM_TURNS):
    print(f"Turn number: {turn_index + 1}")

    nao.buttons.register_callback(touch_stop)

    try:
        if turn_index == 0:
            # First turn: Get a specific historical role
            specific_role = historical_roles.get_role_for_era(FIRST_ERA)
            prompt_for_role = historical_roles.format_as_prompt(specific_role)
            print("Prompt for role:\n", prompt_for_role)

            reply = get_gpt_response(system_input=prompt_for_role)
        else:
            # Subsequent turns
            if interrupted:
                random_role = historical_roles.get_random_role()
                prompt_for_random_role = historical_roles.format_as_prompt(random_role)
                reply = get_gpt_response(system_input=prompt_for_random_role)
                interrupted = False
            else:
                reply = get_gpt_response(system_input="Carry on the previous conversation with the user.")

        # Handle GPT response (may set `interrupted`)
        print("GPT Response:\n", reply)
        handle_gpt_response(reply)

        # Skip listening step if already interrupted
        if not interrupted:
            print("Talk now:")
            set_eye_color("green")  # Indicate NAO is listening
            transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
            user_input = transcript.transcript
            print("Transcript:\n", user_input)

            # Track user responses
            user_responses.append(user_input)

            # Detect disinterest via short responses
            interrupted = detect_disinterest_via_response_length(user_responses)

            if interrupted:
                print("Detected user disinterest based on short responses.")

    except Exception as e:
        print(f"Error during turn {turn_index + 1}: {e}")

    # Reset eye color after each turn
    set_eye_color("blue")

# End conversation
print("Conversation done!")
nao.motion.request(NaoPostureRequest("Sit", 0.5))
set_eye_color("off")  # Optionally turn off LEDs after the conversation
