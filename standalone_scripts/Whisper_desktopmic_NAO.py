import time
from sic_framework.devices import Nao
from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
    Transcript,
    WhisperConf,
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

openai_key = "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"

whisper_conf = WhisperConf(openai_key=openai_key)
whisper = SICWhisper(conf=whisper_conf)

nao = Nao(ip='10.0.0.127')  # Replace with your NAO robot's IP address

desktop = Desktop()
whisper.connect(desktop.mic)
time.sleep(1)

conf = GPTConf(openai_key=openai_key)
gpt = GPT(conf=conf)

NUM_TURNS = 6
i = 0

def send_text_to_nao(text):
    try:
        nao.tts.request(NaoqiTextToSpeechRequest(text))
        print(f"NAO says: {text}")
    except Exception as e:
        print(f"Error sending text to NAO: {e}")

while i < NUM_TURNS:
    print("Talk now!")
    transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
    inp = transcript.transcript
    print("Transcript:", inp)

    try:
        reply = gpt.request(GPTRequest(inp))
        response = reply.response
        print("ChatGPT Response:", response)

        # Send ChatGPT's response to NAO's TTS system
        send_text_to_nao(response)
    except Exception as e:
        print(f"An error occurred: {e}")

    i += 1

print("Conversation done!")
