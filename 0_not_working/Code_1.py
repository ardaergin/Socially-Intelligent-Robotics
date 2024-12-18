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


from nltk.tokenize import sent_tokenize
import nltk

nltk.download('punkt_tab')


def break_into_sentences(text):
    return sent_tokenize(text)

# with starting prompt
conversation = [{"role": "system",
                 "content": "You are a social robot carrying out an experiment. You will only talk to one user at a time. The scenario is that you are a time traveler that has been to different periods in time to amsterdm. Talk with an adventurous tone and use real facts of that time period to tell a story of that time period. Always remain on the topic unless you are asked to change it. Don't talk about sensitive or private information about the user. Ask engaging questions."}]


def converse(user_input):
    conversation.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation,
    )
    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})

    return reply


def system_input(user_input):
    conversation.append({"role": "system", "content": user_input})
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
# nao.buttons.register_callback(touch_stop)

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
            welcome_message = (
                "Hello! I am a social robot, and today, we will time-travel together to explore the fascinating history of Amsterdam.")
            send_sentence_and_animation_to_nao(welcome_message)
            set_eye_color('green')  # NAO eyes turn green to indicate listening
    except queue.Empty:
        print("No face detected yet, still waiting...")
    except Exception as e:
        print(f"Error during face detection: {e}")

# Start the conversation loop
NUM_TURNS = 10
interrupted = False
i = 0

from HistoricalRoles import HistoricalRoles
historical_roles = HistoricalRoles()


while i < NUM_TURNS:
    print("Turn number:", i)

    nao.buttons.register_callback(touch_stop)

    if i == 0:
        specific_role = historical_roles.get_role_for_era("1500s")
        prompt_for_role = historical_roles.format_as_prompt(specific_role)
        print("prompt_for_role: \n")
        print(prompt_for_role)
        
        reply = system_input(prompt_for_role)
        print("ChatGPT Response:", reply)

        gpt_response_in_sentences = break_into_sentences(reply)
        for sentence in gpt_response_in_sentences:
            send_sentence_and_animation_to_nao(sentence)
            if interrupted:
                print("Interruption detected. Responding to touch.")
                # Respond with the touch message
                nao.tts.request(NaoqiTextToSpeechRequest(
                    "Oh, I understand that you are uninterested in this subject, let me switch."))
                break

        print("Talk now:")
        set_eye_color('green')  # Indicate NAO is listening
        transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
        inp = transcript.transcript
        print("Transcript:", inp)
    
    else: 
        if not interrupted:
            reply = converse("Carry on the conversation.")
            print("ChatGPT Response:", reply)

            gpt_response_in_sentences = break_into_sentences(reply)
            for sentence in gpt_response_in_sentences:
                send_sentence_and_animation_to_nao(sentence)
                if interrupted:
                    print("Interruption detected. Responding to touch.")
                    # Respond with the touch message
                    nao.tts.request(NaoqiTextToSpeechRequest(
                        "Oh, I understand that you are uninterested in this subject, let me switch."))
                    break

            print("Talk now:")
            set_eye_color('green')  # Indicate NAO is listening
            transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
            inp = transcript.transcript
            print("Transcript:", inp)
        else: 
            random_role = historical_roles.get_random_role()
            prompt_for_random_role = historical_roles.format_as_prompt(random_role)
            reply = system_input(prompt_for_random_role)
            interrupted = False
            print("ChatGPT Response:", reply)
            gpt_response_in_sentences = break_into_sentences(reply)
            for sentence in gpt_response_in_sentences:
                send_sentence_and_animation_to_nao(sentence)
                if interrupted:
                    print("Interruption detected. Responding to touch.")
                    # Respond with the touch message
                    nao.tts.request(NaoqiTextToSpeechRequest(
                        "Oh, I understand that you are uninterested in this subject, let me switch."))
                    break
            
            print("Talk now:")
            set_eye_color('green')  # Indicate NAO is listening
            transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
            inp = transcript.transcript
            print("Transcript:", inp)

    # Only start listening again after speech completes
    set_eye_color('blue')

    i += 1

print("Conversation done!")
nao.motion.request(NaoPostureRequest("Sit", 0.5))
set_eye_color('off')  # Optionally turn off the LEDs after the conversation
