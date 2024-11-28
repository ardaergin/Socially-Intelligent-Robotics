class HistoricalContextManager:
    def __init__(self):
        self.current_period = None
        self.history_map = {
            "1920s": {
                "events": ["Prohibition", "Women's Suffrage", "The Jazz Age"],
                "figures": ["Al Capone", "F. Scott Fitzgerald", "Louis Armstrong"],
                "culture": ["Flapper fashion", "Silent films", "Art Deco"],
            },
            # Add more historical periods and related topics here
        }

    def suggest_new_topic(self):
        if self.current_period in self.history_map:
            topics = self.history_map[self.current_period]
            return topics
        return {}

    def switch_topic(self, user_input):
        # Analyze user input to determine if a topic switch is needed
        # This could involve NLP analysis or keyword detection
        new_period = self.detect_new_period(user_input)
        if new_period:
            self.current_period = new_period
            return f"Let's explore the {new_period}."
        return "Would you like to explore a different historical period?"

    def detect_new_period(self, user_input):
        # Placeholder for NLP or keyword detection logic
        # Return a new historical period based on user input
        for period in self.history_map:
            if period in user_input:
                return period
        return None 
