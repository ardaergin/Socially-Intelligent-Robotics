import time
import random
import threading
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
        NaoqiTextToSpeechRequest,
        NaoqiTextToSpeechResponse)


def set_eye_color(nao, color):
    """
    Change NAO's eye color.
    """
    if color == 'green':
        nao.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 1, 0, 0))
    elif color == 'blue':
        nao.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 0, 1, 0))
    elif color == 'off':
        nao.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 0, 0, 0))


def play_random_animations(nao, stop_event):
    """
    Play random animations while NAO is speaking.
    """

    while not stop_event.is_set():
        animation_number = random.randint(1, 11)
        animation_path = f"animations/Stand/Gestures/Explain_{animation_number}"
        nao.motion.request(NaoqiAnimationRequest(animation_path))
        time.sleep(random.uniform(2, 4))  # Wait before playing another animation


def send_sentence_to_nao(nao, sentence):
    """
    Send text to NAO's TTS and play animations concurrently.
    """

    stop_event = threading.Event()
    animation_thread = threading.Thread(target=play_random_animations, args=(nao, stop_event,))

    try:
        # Send the TTS request
        response: NaoqiTextToSpeechResponse = nao.tts.request(NaoqiTextToSpeechRequest(sentence))
        print(f"NAO says: {sentence}")

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
