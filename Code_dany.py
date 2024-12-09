import os
import random
import threading
import time
import nltk
from dotenv import load_dotenv
from nltk.tokenize import sent_tokenize
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, OpenAI
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
    WhisperConf,
)
from sic_framework.devices.desktop import Desktop
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

# connect to desktop mic

desktop = Desktop()
whisper.connect(desktop.mic)

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


def add_context_to_conversation(content, role):
    conversation.append({"role": role, "content": content})


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
        nao.tts.request(
            NaoqiTextToSpeechRequest("Oh, I understand. Let me switch to a different time period in Amsterdam."))
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
        "The scenario is that you are a time traveler who has visited different time periods of Amsterdam."
        "You will receive different roles, act appropriately"
        "Talk with an adventurous tone and use real facts of that time period to tell a story. "
        "Always remain on topic unless the user requests to change the topic."
        " Avoid sensitive or private information. Ask engaging questions to guide the conversation."
        "Only ask questions at the end of your reply."
    ),
}
INTRODUCTION_PROMPT = (
    "Introduce yourself and from which time period you are from in 1 or 2 sentences."
)
CONTINUE_CONVERSATION_PROMPT = (
    "Continue the conversation in the respective role."
    "After talking for about three sentences ask an interactive question."
)

for turn_index in range(NUM_TURNS):
    if verbose_output: print(f"Turn number: {turn_index + 1}")

    # reset conversation
    conversation = [CONVERSATION_START_PROMPT]

    # register button interrupt callback
    nao.buttons.register_callback(touch_stop)

    # get random role
    random_role = historical_roles.get_random_role()
    role_prompt = historical_roles.format_as_prompt(random_role)
    add_context_to_conversation(role_prompt, "system")

    # talk loop
    while not interrupted:
        # robot talk code
        reply = get_gpt_response(CONTINUE_CONVERSATION_PROMPT)
        sentences = break_into_sentences(reply)
        set_eye_color('blue')
        for sentence in sentences:
            send_sentence_and_animation_to_nao(sentence)
            if interrupted:
                break
        if interrupted:
            break
        # always end by asking a question and then get response from user
        print("You can talk now:")
        set_eye_color('green')
        transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
        user_input = transcript.transcript
        add_context_to_conversation(user_input, "user")
        if verbose_output: print("Transcript:", user_input)
    interrupted = False

print("Conversation done!")
nao.motion.request(NaoPostureRequest("Sit", 0.5))
set_eye_color('off')
