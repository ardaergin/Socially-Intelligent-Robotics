from .text_to_speech import TextToSpeech
from .speech_to_text import SpeechToText
from .chat_gpt import GPT
from .interruption import Interruption
from ..utils.sentence_utils import break_into_sentences

class Conversation:
    def __init__(self, nao, whisper_key, gpt_key, motion, leds):
        """
        Initialize the Conversation class.

        :param nao: The NAO robot instance.
        :param whisper_key: The OpenAI Whisper API key.
        :param gpt_key: The OpenAI GPT API key.
        :param motion: The Motion instance for animations.
        :param leds: The LED control instance.
        """
        self.tts = TextToSpeech(nao, motion)
        self.stt = SpeechToText(whisper_key)
        self.gpt = GPT(gpt_key, max_history_length=5)
        self.interruption = Interruption(nao, self.tts, self.gpt)
        self.leds = leds

    def start(self, num_turns=3):
        """
        Start the conversation loop.

        :param num_turns: The number of conversation turns.
        """
        for _ in range(num_turns):
            try:
                self.leds.set_eye_color('green')
                transcript = self.stt.transcribe()
                print("Transcript:", transcript.transcript)

                self.leds.set_eye_color('blue')
                response = self.gpt.generate_response(transcript.transcript)
                sentences = break_into_sentences(response)

                for sentence in sentences:
                    self.tts.send_text_and_animation_to_nao(sentence)
                    if self.interruption.interrupted:
                        self.interruption.handle_interrupt()
                        self.interruption.interrupted = False
                        break
            except Exception as e:
                print(f"Error during conversation: {e}")
