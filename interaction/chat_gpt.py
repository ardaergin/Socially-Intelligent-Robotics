import os
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

# Initialize ChatGPT configuration
def initialize_chat_gpt(openai_key, model="gpt-4o-mini", prompt_file="data/prompt_start.txt"):
    gpt = GPT(conf=GPTConf(openai_key=openai_key))
    history = []

    # Load the system prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "..", prompt_file)
    try:
        with open(prompt_path, "r") as file:
            system_prompt = file.read().strip()
    except FileNotFoundError:
        system_prompt = "You are a helpful assistant."
    history.append({"role": "system", "content": system_prompt})

    return gpt, history

# Generate a response from ChatGPT
def generate_response(gpt, history, user_input, model="gpt-4o-mini", max_history_length=5):
    history.append({"role": "user", "content": user_input})

    # Trim history to maintain the maximum number of exchanges
    if len(history) > max_history_length * 2:
        history = [history[0]] + history[-max_history_length * 2:]

    # Send the API request
    response = gpt.request(GPTRequest(messages=history, model=model))
    reply = response.response
    history.append({"role": "assistant", "content": reply})

    return reply, history
