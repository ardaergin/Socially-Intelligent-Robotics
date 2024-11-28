from .text_to_speech import TextToSpeech
from .speech_to_text import SpeechToText
from .chat_gpt import GPT
from .historical_roles import HistoricalRoles
from ..immersive.images import display_image
from ..immersive.sound import play_audio_loop, stop_audio
from .interruption.touch_callback import register_touch_callback
from ..utils.sentence_utils import break_into_sentences
import threading

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
        self.nao = nao
        self.tts = TextToSpeech(nao, motion)
        self.stt = SpeechToText(whisper_key)
        self.gpt = GPT(gpt_key, max_history_length=5)
        self.roles = HistoricalRoles()
        self.leds = leds
        self.current_role = None
        self.interrupted = False

        # Register the touch sensor callback
        register_touch_callback(nao, self._handle_touch_interrupt)

        # Manage media playback threads
        self.image_thread = None
        self.audio_thread = None

    def start(self, num_turns=3):
        """
        Start the conversation loop.

        :param num_turns: The number of conversation turns.
        """
        # Hardcoded welcome message
        welcome_message = (
            "Hello! I am a social robot, and today, we will time-travel together "
            "to explore the fascinating history of Amsterdam. Get ready for an immersive experience!"
        )
        self.tts.send_text_and_animation_to_nao(welcome_message)

        # Conversation loop
        for _ in range(num_turns):
            try:
                # Fetch role data dynamically
                role_data = self._get_current_role()

                # Display image and play audio in threads
                self._start_media_threads(role_data)

                # Introduce the role and context
                intro_text = f"{role_data['role']} {role_data['era_description']}"
                self.tts.send_text_and_animation_to_nao(intro_text)

                # User interaction
                self.leds.set_eye_color('green')
                transcript = self.stt.transcribe()
                print("Transcript:", transcript.transcript)

                self.leds.set_eye_color('blue')
                response = self.gpt.generate_response(transcript.transcript)
                sentences = break_into_sentences(response)

                for sentence in sentences:
                    self.tts.send_text_and_animation_to_nao(sentence)

                    # Check for interruption
                    if self.interrupted:
                        self._handle_interrupt()
                        break

            except Exception as e:
                print(f"Error during conversation: {e}")

    def _get_current_role(self):
        """
        Get the current role, initializing it if not already set.

        :return: The current role data.
        """
        if not self.current_role or self.interrupted:
            self.current_role = self.roles.get_random_role()
        return self.current_role

    def _start_media_threads(self, role_data):
        """
        Start threads for displaying the image and playing audio.

        :param role_data: The role data containing image and audio paths.
        """
        # Stop previous media threads
        self._stop_media_threads()

        # Start image display thread
        if "image" in role_data and role_data["image"]:
            self.image_thread = threading.Thread(target=display_image, args=(role_data["image"],))
            self.image_thread.start()

        # Start audio loop thread
        if "audio" in role_data and role_data["audio"]:
            self.audio_thread = threading.Thread(target=play_audio_loop, args=(role_data["audio"],))
            self.audio_thread.start()

    def _stop_media_threads(self):
        """
        Stop the image and audio threads.
        """
        # Stop audio playback
        stop_audio()
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()

        # Stop image display
        if self.image_thread and self.image_thread.is_alive():
            self.image_thread.join()

    def _handle_interrupt(self):
        """
        Handle the interruption logic by switching to a new role.
        """
        print("Handling interruption...")
        interrupt_response = "Oh, I understand that you are uninterested in this subject, let me switch."
        self.tts.send_text_and_animation_to_nao(interrupt_response)

        # Stop current media
        self._stop_media_threads()

        # Switch to a new role
        self.current_role = self.roles.get_random_role()
        self.interrupted = False

    def _handle_touch_interrupt(self, interrupted):
        """
        Handle the touch interrupt triggered by the external callback.

        :param interrupted: Boolean indicating if the touch interrupt occurred.
        """
        if interrupted:
            self.interrupted = True
            self._stop_media_threads()
