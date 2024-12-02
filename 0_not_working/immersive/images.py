import cv2
import time

def display_images_sequentially(images, duration=5, transition_time=1):
    """
    Display a sequence of images in the same window with a smooth transition.

    :param images: List of image paths to display.
    :param duration: Duration in seconds to display each image.
    :param transition_time: Duration in seconds for the transition effect.
    """
    try:
        # Create a fullscreen window
        cv2.namedWindow("Historical Image", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Historical Image", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        previous_img = None

        for idx, image_path in enumerate(images):
            img = cv2.imread(image_path)
            if img is None:
                print(f"Image not found: {image_path}")
                continue

            # Transition smoothly if there is a previous image
            if previous_img is not None:
                fade_transition(previous_img, img, transition_time)

            # Display the current image
            cv2.imshow("Historical Image", img)
            cv2.waitKey(duration * 1000)  # Display for `duration` seconds

            # Store the current image as the previous image
            previous_img = img

        cv2.destroyAllWindows()
    except Exception as e:
        print(f"Error displaying images: {e}")

def fade_transition(image1, image2, transition_time):
    """
    Create a fade effect between two images.

    :param image1: The first image (numpy array).
    :param image2: The second image (numpy array).
    :param transition_time: Time for the transition effect in seconds.
    """
    try:
        steps = int(transition_time * 30)  # Assuming ~30 frames per second
        for alpha in range(steps + 1):
            blend = cv2.addWeighted(image1, 1 - alpha / steps, image2, alpha / steps, 0)
            cv2.imshow("Historical Image", blend)
            cv2.waitKey(int(1000 / 30))  # Delay for ~30 FPS
    except Exception as e:
        print(f"Error during transition: {e}")
