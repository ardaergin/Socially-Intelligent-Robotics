import random
from ..utils.sentence_utils import break_into_sentences


class Interruption:
    def __init__(self, nao, tts, gpt, historical_roles):
        """
        Initialize the Interruption class.

        :param nao: The NAO robot instance.
        :param tts: The TextToSpeech instance for handling TTS.
        :param gpt: The GPT instance for generating responses.
        :param historical_roles: The HistoricalRoles instance for managing era-specific data.
        """
        self.nao = nao
        self.tts = tts
        self.gpt = gpt
        self.historical_roles = historical_roles
        self.interrupted = False

        # Register the touch sensor callback
        self.nao.buttons.register_callback(self.touch_stop)

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

        # Select a new historical role for the conversation
        new_role_data = self.historical_roles.get_random_role()
        if not new_role_data:
            fallback_response = "I'm sorry, I don't have any topics to discuss right now."
            self.tts.send_text_and_animation_to_nao(fallback_response)
            return

        # Format the new system prompt and update the GPT instance
        new_system_prompt = self.historical_roles.format_as_prompt(new_role_data)
        self.gpt.set_system_prompt(new_system_prompt)

        # Introduce the new role and context
        new_intro_text = f"Now, let's explore the following era:\n{new_role_data['role']} {new_role_data['era_description']}"
        self.tts.send_text_and_animation_to_nao(new_intro_text)

        # Ask an engaging question to continue the interaction
        interactive_question = random.choice(new_role_data['interactive_questions'])
        follow_up_response = self.gpt.generate_response(interactive_question)

        sentences = break_into_sentences(follow_up_response)
        for sentence in sentences:
            self.tts.send_text_and_animation_to_nao(sentence)
