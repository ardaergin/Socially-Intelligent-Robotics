import os 
import time
import queue
import random
import threading
import cv2
import logging
from typing import List, Dict, Optional

# Use more robust environment variable management
from dotenv import load_dotenv
from decouple import config

# Enhanced device and service imports
from sic_framework.devices import Nao
from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript, SICWhisper, WhisperConf
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, OpenAI
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.services.face_detection.face_detection import FaceDetection
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage, CompressedImageMessage
)
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest

# Enhanced Natural Language Processing
import nltk
from nltk.tokenize import sent_tokenize

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nao_robot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Centralized configuration management for the NAO robot system."""
    @staticmethod
    def load_configuration():
        """Load and validate configuration from environment."""
        try:
            load_dotenv()
            return {
                'openai_key': config('OPENAI_KEY', default=None, cast=str),
                'nao_ip': config('NAO_IP', default=None, cast=str),
                'gpt_model': config('GPT_MODEL', default='gpt-4o-mini', cast=str),
                'max_conversation_turns': config('MAX_CONVERSATION_TURNS', default=10, cast=int)
            }
        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            raise EnvironmentError("Invalid or missing configuration")

class NAOInteractionManager:
    def __init__(self, config: Dict):
        """
        Initialize NAO interaction system with robust error handling.
        
        :param config: Configuration dictionary
        """
        try:
            self.config = config
            
            # Robust device and service initialization
            self.nao = Nao(ip=self.config['nao_ip'])
            self.desktop = Desktop(
                camera_conf=DesktopCameraConf(fx=1.0, fy=1.0, flip=1)
            )
            
            # Initialize services with error handling
            self.initialize_services()
            
            # Initialize buffers and event management
            self.imgs_buffer = queue.Queue(maxsize=1)
            self.faces_buffer = queue.Queue(maxsize=1)
            self.interrupted = threading.Event()
            
            # Register callbacks
            self.register_callbacks()
            
            logger.info("NAO Interaction System initialized successfully")
        
        except Exception as e:
            logger.critical(f"Initialization failed: {e}")
            raise

    def initialize_services(self):
        """Initialize and connect all required services."""
        try:
            self.face_rec = FaceDetection()
            self.whisper = SICWhisper(
                conf=WhisperConf(openai_key=self.config['openai_key'])
            )
            self.gpt = GPT(
                conf=GPTConf(
                    openai_key=self.config['openai_key'], 
                    model=self.config['gpt_model']
                )
            )
            self.openai_client = OpenAI(api_key=self.config['openai_key'])

            # Service connection with robust error handling
            services = [
                (self.face_rec, self.desktop.camera),
                (self.whisper, self.desktop.mic)
            ]
            
            for service, device in services:
                try:
                    service.connect(device)
                    logger.info(f"Connected {service.__class__.__name__}")
                except Exception as conn_error:
                    logger.warning(f"Could not connect {service.__class__.__name__}: {conn_error}")
        
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            raise

    def register_callbacks(self):
        """Register device and service callbacks."""
        self.desktop.camera.register_callback(self.on_image)
        self.face_rec.register_callback(self.on_faces)
        self.nao.buttons.register_callback(self.touch_stop)

    def on_image(self, image_message: CompressedImageMessage):
        """Handle incoming images."""
        try:
            self.imgs_buffer.put(image_message.image)
        except Exception as e:
            logger.error(f"Image processing error: {e}")

    def on_faces(self, message: BoundingBoxesMessage):
        """Handle face detection."""
        try:
            self.faces_buffer.put(message.bboxes)
        except Exception as e:
            logger.error(f"Face detection error: {e}")

    def touch_stop(self, event):
        """Handle touch interruption."""
        try:
            sensor = event.value
            touch_detection = any(sensor_info[1] for sensor_info in sensor)
            
            if touch_detection:
                logger.info("Touch interruption detected")
                self.interrupted.set()
        except Exception as e:
            logger.error(f"Touch detection error: {e}")

def main():
    """Main execution method for NAO social robot interaction."""
    try:
        # Load configuration
        config = ConfigurationManager.load_configuration()
        
        # Initialize interaction manager
        interaction_manager = NAOInteractionManager(config)
        
        # Prepare for interaction
        interaction_manager.nao.motion.request(NaoPostureRequest("Stand", 0.5))
        
        # Wait for face detection
        logger.info("Waiting for face detection to start conversation...")
        interaction_loop(interaction_manager)
    
    except Exception as e:
        logger.critical(f"Fatal error in main execution: {e}")

def interaction_loop(interaction_manager):
    """
    Manage interaction loop with robust error handling.
    
    :param interaction_manager: NAOInteractionManager instance
    """
    try:
        face_detected = False
        while not face_detected:
            try:
                img = interaction_manager.imgs_buffer.get(timeout=5)
                faces = interaction_manager.faces_buffer.get(timeout=5)

                if faces:
                    logger.info("Face detected! Starting conversation...")
                    face_detected = True
                    start_conversation(interaction_manager)
            except queue.Empty:
                logger.info("No face detected yet, still waiting...")
            except Exception as e:
                logger.error(f"Face detection error: {e}")
    except Exception as e:
        logger.critical(f"Interaction loop failed: {e}")

def start_conversation(interaction_manager):
    """
    Initiate and manage conversation with robust error handling.
    
    :param interaction_manager: NAOInteractionManager instance
    """
    try:
        # Welcome sequence
        interaction_manager.set_eye_color('green')
        welcome_message = (
            "Hello! I am a social robot, and today, "
            "we will time-travel together to explore the fascinating history of Amsterdam. "
            "Get ready for an immersive experience!"
        )
        send_sentence_and_animation_to_nao(welcome_message)
        
        # Conversation management
        conversation_turns = interaction_manager.config['max_conversation_turns']
        conversation_loop(interaction_manager, conversation_turns)
    
    except Exception as e:
        logger.error(f"Conversation start failed: {e}")
    finally:
        # Cleanup and reset
        interaction_manager.nao.motion.request(NaoPostureRequest("Sit", 0.5))
        interaction_manager.set_eye_color('off')

def conversation_loop(interaction_manager, turns):
    """Manage conversation turns with error resilience."""
    # Implementation would follow similar patterns to previous code
    pass

if __name__ == "__main__":
    main()
