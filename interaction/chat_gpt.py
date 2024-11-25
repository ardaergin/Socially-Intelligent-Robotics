import os
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

class GPT:
    def __init__(self, openai_key, model="gpt-4o-mini", max_history_length=5, prompt_file="data/prompt_start.txt"):
        """
        Initialize the GPT instance with API key and history management.

        :param openai_key: API key for OpenAI.
        :param model: ChatGPT model to use.
        :param max_history_length: Maximum number of exchanges to keep in the history.
        :param prompt_file: Path to the file containing the system prompt.
        """
        self.gpt = GPT(conf=GPTConf(openai_key=openai_key))
        self.model = model
        self.history = []  # List to store conversation history as {"role": ..., "content": ...}
        self.max_history_length = max_history_length

        # Load the system prompt and add it to the conversation history
        self._load_system_prompt(prompt_file)

    def _load_system_prompt(self, prompt_file):
        """
        Load the system prompt from a file and add it as the first message in the conversation.

        :param prompt_file: Path to the file containing the system prompt.
        """
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), "..", prompt_file)
            with open(prompt_path, "r") as file:
                system_prompt = file.read().strip()
            self.history.append({"role": "system", "content": system_prompt})
        except FileNotFoundError:
            print(f"Prompt file '{prompt_file}' not found. Using default system prompt.")
            self.history.append({"role": "system", "content": "You are a helpful assistant."})

    def generate_response(self, user_input):
        """
        Generate a response from ChatGPT, considering the conversation history.

        :param user_input: The user's input.
        :return: The response from ChatGPT.
        """
        # Add user input to the conversation history
        self.history.append({"role": "user", "content": user_input})

        # Trim the conversation history to maintain the maximum length
        self._trim_history()

        # Make the API request
        response = self.gpt.request(GPTRequest(messages=self.history, model=self.model))

        # Extract the assistant's reply
        reply = response.response  # Assuming GPTRequest returns this
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def _trim_history(self):
        """
        Trim the conversation history to maintain the maximum number of exchanges.
        """
        max_messages = self.max_history_length * 2  # Each turn has 2 messages: user and assistant
        if len(self.history) > max_messages:
            # Preserve the system message while trimming user and assistant exchanges
            self.history = [self.history[0]] + self.history[-max_messages:]

