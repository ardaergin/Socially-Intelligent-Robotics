from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    SICWhisper, WhisperConf, GetTranscript
)


class SpeechToText:
    def __init__(self, openai_key):
        self.whisper = SICWhisper(conf=WhisperConf(openai_key=openai_key))

    def transcribe(self, timeout=10, phrase_time_limit=30):
        return self.whisper.request(GetTranscript(timeout=timeout, phrase_time_limit=phrase_time_limit))
