

import os
import json
import random


class HistoricalRoles:
    def __init__(self):
        """
        Initialize the HistoricalRoles class.
        """
        self.roles = self._load_roles()
        self.previous_eras = []  # List to store previously chosen eras
        self.current_role = None  # Store the current role

    def _load_roles(self):
        """
        Load historical roles from a JSON file.

        :return: Dictionary of roles by era.
        """
        roles_path = os.path.join(os.path.dirname(__file__), "data", "amsterdam_eras.json")
        try:
            with open(roles_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Roles file {roles_path} not found.")
            return {}

    def get_random_role(self):
        """
        Get a random historical role from the available eras, excluding the ones already chosen.
        Updates the current_role with the chosen role.

        :return: A dictionary containing role, era description, interactive questions, and dialogue style.
        """
        if not self.roles:
            return None
        remaining_eras = list(set(self.roles.keys()) - set(self.previous_eras))
        
        if not remaining_eras:
            print("All eras have been chosen.")
            return None
        
        era = random.choice(remaining_eras)
        self.previous_eras.append(era)  # Add the chosen era to the previous_eras list
        self.current_role = self.roles[era]  # Update the current_role
        return self.current_role

    def get_role_for_era(self, era):
        """
        Get the historical role for a specific era and update the previous_eras list.
        Updates the current_role with the chosen role.

        :param era: The era for which the role should be retrieved (e.g., "1500s", "1600s").
        :return: A dictionary containing role, era description, interactive questions, and dialogue style, or None if the era is not found.
        """
        if era in self.roles:
            self.previous_eras.append(era)  # Add the chosen era to the previous_eras list
            self.current_role = self.roles[era]  # Update the current_role
            return self.current_role
        else:
            print(f"No role found for the era: {era}")
            return None

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

    def get_current_role(self):
        """
        Returns the current role.

        :return: The current role data.
        """
        return self.current_role


# if __name__ == "__main__":
#     historical_roles = HistoricalRoles()
#     random_role = historical_roles.get_random_role()
#     prompt_for_random_role = historical_roles.format_as_prompt(random_role)
#     print(prompt_for_random_role)
