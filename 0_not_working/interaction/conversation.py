from immersive.images import display_images_sequentially
from immersive.sound import play_audio_loop, stop_audio
from .historical_roles import HistoricalRoles
from .interruption.touch_callback import register_touch_callback
from .speech_to_text import SpeechToText
from .text_to_speech import send_text_to_nao
from .chat_gpt import initialize_chat_gpt, generate_response
import threading


class Conversation:
    def __init__(self, nao, whisper_key, gpt_key, motion, leds):
        self.nao = nao
        self.motion = motion
        self.leds = leds
        self.stt = SpeechToText(whisper_key)
        self.roles = HistoricalRoles()
        self.current_role = None
        self.interrupted = False

        # Register touch interrupt
        register_touch_callback(nao, self._handle_touch_interrupt)

        # Initialize ChatGPT
        self.gpt, self.history = initialize_chat_gpt(gpt_key)

        # Manage media playback threads
        self.media_thread = None
        self.audio_thread = None

    def start(self):
        while True:
            try:
                # Fetch current role
                role_data = self._get_current_role()

                # Display media
                self._start_media_threads(role_data)

                # Introduce role
                intro_text = f"{role_data['role']} {role_data['era_description']}"
                send_text_to_nao(self.nao, self.motion, intro_text)

                # Listen and respond
                self.leds.set_eye_color("green")
                transcript = self.stt.transcribe().transcript
                print(f"User: {transcript}")

                # Detect Short Response
                if len(transcript.split()) < 5:
                    print("Detected User gave a short response...")
                    self._handle_short_response()

                self.leds.set_eye_color("blue")
                response, self.history = generate_response(self.gpt, self.history, transcript)
                send_text_to_nao(self.nao, self.motion, response)

                # Check for interruption
                if self.interrupted:
                    self._handle_interrupt()
            except Exception as e:
                print(f"Error in conversation: {e}")

    def _get_current_role(self):
        if not self.current_role or self.interrupted:
            self.current_role = self.roles.get_random_role()
        return self.current_role

    def _start_media_threads(self, role_data):
        self._stop_media_threads()

        # Start image thread
        if "image" in role_data and isinstance(role_data["image"], list):
            self.media_thread = threading.Thread(
                target=display_images_sequentially, args=(role_data["image"],)
            )
            self.media_thread.start()

        # Start audio thread
        if "audio" in role_data and role_data["audio"]:
            self.audio_thread = threading.Thread(
                target=play_audio_loop, args=(role_data["audio"],)
            )
            self.audio_thread.start()

    def _stop_media_threads(self):
        stop_audio()
        if self.media_thread and self.media_thread.is_alive():
            self.media_thread.join()
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()

    def _handle_interrupt(self):
        send_text_to_nao(
            self.nao, self.motion, "Oh, I understand that you are uninterested in this subject, let me switch."
        )
        self._stop_media_threads()
        self.interrupted = False
        self.current_role = self.roles.get_random_role()

    def _handle_touch_interrupt(self, interrupted):
        if interrupted:
            self.interrupted = True

    def _handle_short_response(self):
        """When short response detected, switch topic"""
        print("Handling short response..")

        # Nao Response
        interrupt_response = "Anyway, let's talk about another era."  # Implicit Switch
        # interrupt_response = ("Oh, I have detected that you are uninterested in this subject, "
        #                       "let's talk about something else.")      # Explicit Switch
        self.tts.send_text_and_animation_to_nao(interrupt_response)

        # Switch to a new role
        self.current_role = self.roles.get_random_role()
