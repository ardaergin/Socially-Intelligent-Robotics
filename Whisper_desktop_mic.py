import time

from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
    Transcript,
    WhisperConf,
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

openai_key = "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"

whisper_conf = WhisperConf(openai_key=openai_key)
whisper = SICWhisper(conf=whisper_conf)

desktop = Desktop()

whisper.connect(desktop.mic)
time.sleep(1)

conf = GPTConf(openai_key=openai_key)
gpt = GPT(conf=conf)

NUM_TURNS = 6
i = 0

while i < NUM_TURNS:
    print("Talk now!")

    transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
    inp = transcript.transcript

    print("Transcript:", inp)

    try:
        reply = gpt.request(GPTRequest(inp))
        print("ChatGPT Response:", reply.response, "\n", sep="")
    except Exception as e:
        print(f"An error occurred: {e}")

    i += 1

print("Conversation done!")
