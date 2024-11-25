import queue

# Initialize buffers for images and face detection
imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)
interrupted = False  # Global flag to detect interruption


def on_image(image_message):
    """
    Callback function for image messages.
    """
    imgs_buffer.put(image_message.image)


def on_faces(message):
    """
    Callback function for face detection messages.
    """
    faces_buffer.put(message.bboxes)


def touch_stop(event, nao):
    """
    Callback function for touch events.
    """
    global interrupted
    sensor = event.value
    print(f"sensor info 0: {sensor[0]}")
    print(f"sensor info 1: {sensor[1]}")
    print(event.value)

    # Detect if any touch sensor is activated
    touch_detection = any(sensor_info[1] == True for sensor_info in sensor)

    if touch_detection:
        print("Touch detected! Stopping current speech and setting interruption flag.")
        # Stop the current speech (if possible)
        # nao.tts.stop()
        # Set the interruption flag
        interrupted = True
