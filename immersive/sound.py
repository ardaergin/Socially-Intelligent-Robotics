import pygame
import time


def play_audio_loop(audio_path):
    """
    Play an audio file in a loop using Pygame.

    :param audio_path: Path to the audio file.
    """
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play(-1)  # -1 means looping indefinitely
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)  # Prevent excessive CPU usage
    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        pygame.mixer.quit()


def stop_audio():
    """
    Stop the currently playing audio.
    """
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"Error stopping audio: {e}")
