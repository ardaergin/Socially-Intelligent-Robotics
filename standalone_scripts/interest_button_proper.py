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
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)
from sic_framework.services.face_detection.face_detection import FaceDetection
from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest

openai_key = "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"

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
gpt_conf = GPTConf(openai_key=openai_key)
gpt = GPT(conf=gpt_conf)

nao = Nao(ip="10.0.0.239")  # Replace with your NAO robot's IP

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
        time.sleep(random.uniform(2, 4))  # Wait a bit before playing another animation


from nltk.tokenize import sent_tokenize
def break_up_response_into_sentences(text):
    sentences = sent_tokenize(text)
    return sentences


# Function to send text to NAO's TTS and play animations concurrently
def send_text_to_nao(text):
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=play_random_animations, args=(stop_event,))

    try:
        # Send the TTS request
        for sentence in text:

            response: NaoqiTextToSpeechResponse = nao.tts.request(NaoqiTextToSpeechRequest(sentence))
            print(f"NAO says: {text}")

            touch_detection = any(sensor_info[1] == True for sensor_info in sensor)

            if touch_detection:
                nao.tts.request(NaoqiTextToSpeechRequest(
                    "Oh, I understand you would like to change the topic. How about we talk about the twenties?"))

            nao.buttons.register_callback(button_function)

            def test_func(event):
                sensor = event.value
                print(f"sensor info 0: {sensor[0]}")
                print(f"sensor info 1: {sensor[1]}")

                print(event.value)


                    # add a confirmation button

            nao = Nao(ip="10.0.0.222")

            nao.buttons.register_callback(test_func)



        # Start the animation thread
        animation_thread.start()

        # Wait until the TTS response indicates completion
        while not response.completed:
            time.sleep(0.1)  # Check at intervals to avoid busy-waiting

        # Signal the animation thread to stop
        stop_event.set()
        animation_thread.join()
    except Exception as e:
        print(f"Error sending text to NAO: {e}")

def button_function(event):
    sensor = event.value
    print(f"sensor info 0: {sensor[0]}")
    print(f"sensor info 1: {sensor[1]}")

    print(event.value)

    touch_detection = any(sensor_info[1] == True for sensor_info in sensor)

    if touch_detection:
        nao.tts.request(NaoqiTextToSpeechRequest("Oh, I understand you would like to change the topic. How about we talk about the twenties?"))


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
            set_eye_color('green')  # NAO eyes turn green to indicate listening
            send_text_to_nao("Hello, I see you! Let's have a conversation.")
    except queue.Empty:
        print("Waiting for face detection...")
    except Exception as e:
        print(f"Error during face detection: {e}")

# Start the conversation loop
NUM_TURNS = 3

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
        reply = gpt.request(GPTRequest(inp))
        response = reply.response
        print("ChatGPT Response:", response)

        # Send ChatGPT's response to NAO's TTS and wait until it finishes, playing animations
        sentences = break_up_response_into_sentences(response)
        send_text_to_nao(sentences)

        # Only start listening again after speech completes
        set_eye_color('green')
    except Exception as e:
        print(f"An error occurred during the conversation: {e}")

    i += 1

print("Conversation done!")
nao.motion.request(NaoPostureRequest("Stand", 0.5))
set_eye_color('off')  # Optionally turn off the LEDs after the conversation
