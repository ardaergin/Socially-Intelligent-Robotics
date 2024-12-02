import threading
import time
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

def send_text_to_nao(nao, motion, text):
    """
    Send text to NAO for TTS with animations.
    """
    stop_event = threading.Event()

    # Play animations in parallel
    animation_thread = threading.Thread(
        target=play_random_animations, args=(motion, stop_event)
    )
    animation_thread.start()

    try:
        # Send the text to NAO's TTS
        response = nao.tts.request(NaoqiTextToSpeechRequest(text))
        print(f"NAO says: {text}")

        # Wait for TTS to complete
        while not response.completed:
            time.sleep(0.1)
    except Exception as e:
        print(f"Error in TTS: {e}")
    finally:
        # Stop animations
        stop_event.set()
        animation_thread.join()

def play_random_animations(motion, stop_event):
    """
    Play random animations while TTS is active.
    """
    import random

    while not stop_event.is_set():
        animation_number = random.randint(1, 11)
        motion.play_animation(f"animations/Stand/Gestures/Explain_{animation_number}")
        time.sleep(random.uniform(2, 4))
