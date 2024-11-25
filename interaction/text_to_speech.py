import threading
import time
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

class TextToSpeech:
    def __init__(self, nao, motion):
        """
        Initialize the TextToSpeech class.

        :param nao: The NAO robot instance.
        :param motion: The Motion class instance for playing animations.
        """
        self.nao = nao
        self.motion = motion

    # Function to send text to NAO's TTS and play animations concurrently
    def send_text_and_animation_to_nao(self, text):
        """
        Send a text message to NAO's TTS system and play animations concurrently.

        :param text: The text to be spoken by NAO.
        """
        stop_event = threading.Event()
        animation_thread = threading.Thread(target=self.motion.play_random_animations, args=(stop_event,))

        try:
            # Start the animation thread
            animation_thread.start()

            # Send the TTS request
            response = self.nao.tts.request(NaoqiTextToSpeechRequest(text))
            print(f"NAO says: {text}")

            # Wait until the TTS response indicates completion
            while not response.completed:
                time.sleep(0.1)  # Check at intervals to avoid busy-waiting

            # Signal the animation thread to stop once NAO finishes speaking
            stop_event.set()
            animation_thread.join()
        except Exception as e:
            print(f"Error sending text to NAO: {e}")
        finally:
            # Ensure the thread is stopped even if an error occurs
            stop_event.set()
            if animation_thread.is_alive():
                animation_thread.join()
