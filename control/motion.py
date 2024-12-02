import time
import random
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest

class Motion:
    def __init__(self, nao):
        self.nao = nao
    
    def set_posture(self, posture, speed=0.5):
        """Set the posture of the robot."""
        self.nao.motion.request(NaoPostureRequest(posture, speed))
    
    def play_animation(self, animation_path):
        """Play a specific animation."""
        self.nao.motion.request(NaoqiAnimationRequest(animation_path))
    
    def play_random_animations(self, stop_event):
        """Play random animations in a loop until stop_event is set."""
        while not stop_event.is_set():
            animation_number = random.randint(1, 11)
            animation_path = f"animations/Stand/Gestures/Explain_{animation_number}"
            self.play_animation(animation_path)
            time.sleep(random.uniform(1, 2))  # Pause before playing another animation
