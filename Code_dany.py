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


def get_gpt_response(text_input, role="user"):
    conversation.append({"role": "user", "content": text_input})
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
    # Detect if ANY touch sensor is activated
    touch_detection = any(sensor_info[1] for sensor_info in sensor)

    if touch_detection:
        if verbose_output: print("Touch detected! Stopping current speech and setting interruption flag.")
        interrupted = True

    #####################
    # conversation loop #
    #####################


verbose_output = False
historical_roles = HistoricalRoles()
NUM_TURNS = 10
interrupted = False
i = 0
# with starting prompt
CONVERSATION_START_PROMPT = {
    "role": "system",
    "content": (
        "You are a social robot carrying out an experiment. You will only talk to one user at a time. "
        "The scenario is that you are a time traveler who has visited different periods of Amsterdam. "
        "You will receive different roles, act appropriately"
        "Talk with an adventurous tone and use real facts of that time period to tell a story. "
        "Always remain on topic unless the user requests to change the topic."
        " Avoid sensitive or private information. Ask engaging questions to guide the conversation."
    ),
}
conversation = [CONVERSATION_START_PROMPT]

for turn_index in range(NUM_TURNS):
    if verbose_output: print(f"Turn number: {turn_index + 1}")

    # register button interrupt callback
    nao.buttons.register_callback(touch_stop)

    # get random role
    random_role = historical_roles.get_random_role()
    prompt_for_random_role = historical_roles.format_as_prompt(random_role)

    # talk loop
    while not interrupted:
        pass

        # always end by asking a question:
        print("You can talk now:")
        set_eye_color('green')  # Indicate NAO is listening
        transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
        inp = transcript.transcript
        if verbose_output: print("Transcript:", inp)

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
