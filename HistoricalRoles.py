import os
import json
import random


class HistoricalRoles:
    def __init__(self):
        """
        Initialize the HistoricalRoles class.

        :param roles_file: Path to the JSON file containing historical roles.
        """
        self.roles = self._load_roles()

    def _load_roles(self):
        """
        Load historical roles from a JSON file.

        :param roles_file: Path to the JSON file containing historical roles.
        :return: Dictionary of roles by era.
        """
        roles_path = os.path.join(os.path.dirname(__file__), "data", "amsterdam_eras.json")
        # roles_path = "./data/amsterdam_eras.json"
        try:
            with open(roles_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Roles file {roles_path} not found.")
            return {}

    def get_random_role(self):
        """
        Get a random historical role from the available eras.

        :return: A dictionary containing role, era description, interactive questions, and dialogue style.
        """
        if not self.roles:
            return None
        era = random.choice(list(self.roles.keys()))
        return self.roles[era]

    def format_as_prompt(self, role_data):
        """
        Format the role data into a ChatGPT-compatible system prompt.

        :param role_data: A dictionary containing role, era description, questions, and dialogue style.
        :return: A string system prompt for ChatGPT.
        """
        if not role_data:
            return "You are a historian in Amsterdam. Engage with the user using your knowledge of Amsterdam's history."

        return (
            f"You are role-playing as:\n"
            f"{role_data['role']}\n\n"
            f"Era Description:\n{role_data['era_description']}\n\n"
            f"Interactive Questions to guide the conversation:\n"
            f"{' '.join(role_data['interactive_questions'])}\n\n"
            f"Dialogue Style:\n"
            f"{' '.join(role_data['dialogue_style'])}\n\n"
            f"Stay in character and engage the user interactively."
        )