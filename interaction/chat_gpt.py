from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

class GPT:
    def __init__(self, openai_key, model="gpt-4o-mini", max_history_length=5):
        """
        Initialize the GPT instance with API key and history management.

        :param openai_key: API key for OpenAI.
        :param max_history_length: Maximum number of exchanges to keep in the history.
        """
        self.gpt = GPT(conf=GPTConf(openai_key=openai_key))
        self.model = model
        self.history = []  # List to store conversation history
        self.max_history_length = max_history_length

    def generate_response(self, prompt):
        """
        Generate a response from ChatGPT, considering the conversation history.

        :param prompt: The user's input.
        :return: The response from ChatGPT.
        """
        # Construct the full prompt including the history
        full_prompt = self._construct_prompt(prompt)

        # Make the API request
        reply = self.gpt.request(GPTRequest(full_prompt, model=self.model))
        
        # Append the new exchange to the history
        self._update_history(prompt, reply.response)
        
        return reply.response

    def _construct_prompt(self, user_input):
        """
        Construct the prompt by including the conversation history.

        :param user_input: The user's current input.
        :return: The full prompt including the history and current input.
        """
        # Combine history and current input
        history_text = "\n".join(self.history)
        full_prompt = f"{history_text}\nUser: {user_input}\nChatGPT:"
        return full_prompt

    def _update_history(self, user_input, response):
        """
        Update the conversation history.

        :param user_input: The user's current input.
        :param response: The response from ChatGPT.
        """
        # Add the new exchange to the history
        self.history.append(f"User: {user_input}")
        self.history.append(f"ChatGPT: {response}")

        # Trim the history to maintain the maximum length
        if len(self.history) > self.max_history_length * 2:  # Multiply by 2 (user+ChatGPT for each exchange)
            self.history = self.history[-self.max_history_length * 2:]
