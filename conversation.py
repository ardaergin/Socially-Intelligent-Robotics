from utils import break_into_sentences
from nao_control import set_eye_color, send_sentence_to_nao

def start_conversation(nao, whisper, gpt, num_turns, interrupted_flag):
    """
    Starts the conversation loop.
    """
    i = 0
    while i < num_turns:
        print("Talk now!")
        try:
            # Ensure listening only starts after NAO finishes speaking
            set_eye_color(nao, 'green')  # Indicate NAO is listening
            transcript = whisper.request_transcript()
            inp = transcript.transcript
            print("Transcript:", inp)

            # Change NAO's eye color to blue while talking
            set_eye_color(nao, 'blue')
            response = gpt.get_response(inp)
            gpt_response_in_sentences = break_into_sentences(response)
            print("ChatGPT Response:", response)

            # Send ChatGPT's response to NAO's TTS and wait until it finishes, playing animations
            for sentence in gpt_response_in_sentences:
                send_sentence_to_nao(nao, sentence)
                if interrupted_flag[0]:
                    print("Interruption detected. Responding to touch.")
                    # Respond with the touch message
                    nao.tts.request(
                        NaoqiTextToSpeechRequest(
                            "Oh, I understand that you're uninterested in this subject, let me switch."
                        )
                    )
                    break

            # Only start listening again after speech completes
            set_eye_color(nao, 'green')

            if interrupted_flag[0]:
                response = gpt.get_response("Can you tell a story about the Roman Empire?")
                gpt_response_in_sentences = break_into_sentences(response)
                print("ChatGPT Response:", response)
                interrupted_flag[0] = False

        except Exception as e:
            print(f"An error occurred during the conversation: {e}")

        i += 1

    print("Conversation done!")
    nao.motion.request(NaoPostureRequest("Stand", 0.5))
    set_eye_color(nao, 'off')  # Optionally turn off the LEDs after the conversation
