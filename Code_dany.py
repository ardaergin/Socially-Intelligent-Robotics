import os
import random
import threading
import time
import nltk
from nltk.tokenize import sent_tokenize
from sic_framework.devices import Nao
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)
from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, OpenAI
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
    WhisperConf,
)
from dotenv import load_dotenv
from HistoricalRoles import HistoricalRoles

nltk.download('punkt_tab')


# Environment Variables
load_dotenv()
openai_key = os.getenv("OPENAI_KEY")
nao_ip = os.getenv("NAO_IP")

if not openai_key or not nao_ip:
    raise EnvironmentError("Missing environment variables in .env file.")

nao = Nao(ip=nao_ip)
nao.motion.request(NaoPostureRequest("Stand", 0.5))

# Initialize devices and services
whisper_conf = WhisperConf(openai_key=openai_key)
whisper = SICWhisper(conf=whisper_conf)
gpt_conf = GPTConf(openai_key=openai_key, model="gpt-4o-mini")
gpt = GPT(conf=gpt_conf)
client = OpenAI(api_key=openai_key)


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
        time.sleep(random.random())


# Function to send sentence to NAO's TTS and play animations concurrently
def send_sentence_and_animation_to_nao(sentence):
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=play_random_animations, args=(stop_event,))

    try:
        animation_thread.start()
        # Send the TTS request
        nao.tts.request(NaoqiTextToSpeechRequest(sentence))
        print(f"NAO says: {sentence}")

        stop_event.set()
        animation_thread.join()
    except Exception as e:
        print(f"Error sending sentence to NAO: {e}")
    finally:
        stop_event.set()
        if animation_thread.is_alive():
            animation_thread.join()


def break_into_sentences(text):
    return sent_tokenize(text)


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






# Start the conversation loop
historical_roles = HistoricalRoles()
NUM_TURNS = 10
interrupted = False
i = 0
# with starting prompt
conversation = [{"role": "system",
                 "content": "You are a social robot carrying out an experiment. You will only talk to one user at a time. The scenario is that you are a time traveler that has been to different periods in time to amsterdm. Talk with an adventurous tone and use real facts of that time period to tell a story of that time period. Always remain on the topic unless you are asked to change it. Don't talk about sensitive or private information about the user. Ask engaging questions."}]



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
