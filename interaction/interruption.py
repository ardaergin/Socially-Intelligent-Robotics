import json
import random
import os
from ..utils.sentence_utils import break_into_sentences

class Interruption:
    def __init__(self, nao, tts, gpt, prompts_file="data/history_topic_prompts.json"):
        """
        Initialize the Interruption class.

        :param nao: The NAO robot instance.
        :param tts: The TextToSpeech instance for handling TTS.
        :param gpt: The GPT instance for generating responses.
        :param prompts_file: Path to the JSON file containing prompts.
        """
        self.nao = nao
        self.tts = tts
        self.gpt = gpt
        self.interrupted = False
        self.prompts = self._load_prompts(prompts_file)
        self.used_prompts = set()  # Keep track of used prompts

        # Register the touch sensor callback
        self.nao.buttons.register_callback(self.touch_stop)

    def _load_prompts(self, prompts_file):
        """
        Load prompts from a JSON file.

        :param prompts_file: Path to the JSON file containing prompts.
        :return: A list of prompts.
        """
        # Get the absolute path of the JSON file
        prompts_path = os.path.join(os.path.dirname(__file__), "..", prompts_file)
        try:
            with open(prompts_path, "r") as file:
                data = json.load(file)
                return data.get("prompts", [])
        except FileNotFoundError:
            print(f"Prompts file '{prompts_path}' not found.")
            return []

    def _get_next_prompt(self):
        """
        Get the next unused prompt or reset the used prompts if all have been used.

        :return: A topic prompt.
        """
        unused_prompts = [prompt for prompt in self.prompts if prompt not in self.used_prompts]

        if not unused_prompts:
            # Reset the used prompts if all have been used
            print("All prompts have been used. Resetting the prompt list.")
            self.used_prompts.clear()
            unused_prompts = self.prompts

        selected_prompt = random.choice(unused_prompts)
        self.used_prompts.add(selected_prompt)
        return selected_prompt

    def touch_stop(self, event):
        """
        Callback function for handling touch events.

        :param event: The touch event data.
        """
        sensor = event.value
        print("Sensor info:", sensor)
        if any(sensor_info[1] for sensor_info in sensor):
            print("Touch detected! Interrupting...")
            self.interrupted = True

    def handle_interrupt(self):
        """
        Handle the interruption logic by sending an alternative response and switching topics.
        """
        print("Handling interruption...")
        interrupt_response = "Oh, I understand that you are uninterested in this subject, let me switch."
        self.tts.send_text_and_animation_to_nao(interrupt_response)

        if self.prompts:
            # Select the next unused prompt
            random_prompt = self._get_next_prompt()
            print(f"Selected prompt: {random_prompt}")

            # Generate a follow-up response based on the selected prompt
            follow_up = self.gpt.generate_response(random_prompt)
            sentences = break_into_sentences(follow_up)

            for sentence in sentences:
                self.tts.send_text_and_animation_to_nao(sentence)
        else:
            # Handle the case where no prompts are available
            fallback_response = "I'm sorry, I don't have any topics to discuss right now."
            self.tts.send_text_and_animation_to_nao(fallback_response)
