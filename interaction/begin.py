import queue

def detect_face_and_welcome(nao, led_control, faces_buffer):
    """
    Detects a face and welcomes the user.

    :param nao: The NAO robot instance.
    :param led_control: The LEDControl instance to manage LED colors.
    :param faces_buffer: Queue to retrieve face detection results.
    """
    print("Waiting for a face to start the interaction...")
    while True:
        try:
            # Try retrieving face detection results
            faces = faces_buffer.get(timeout=5)
            if faces:
                print("Face detected! Starting interaction...")
                # Greet the user
                welcome_message = (
                    "Hello! I am a social robot, and today, we will time-travel together "
                    "to explore the fascinating history of Amsterdam. Get ready for an immersive experience!"
                )
                nao.tts.request(welcome_message)  # Send the welcome message
                led_control.set_eye_color("green")  # Turn eyes green to indicate readiness
                break
        except queue.Empty:
            print("No face detected yet, still waiting...")
        except Exception as e:
            print(f"Error during face detection: {e}")
            break
