
from sic_framework.devices import Nao

nao = Nao(ip="10.0.0.240")

def test_func(a):
    print("Pressed", a.value)

def touch_stop(sensor):
    # global interrupted
    sensor = sensor.value
    print("Pressed", sensor.value)
    
    # # Detect if ANY touch sensor is activated
    # touch_detection = any(sensor_info[1] for sensor_info in sensor)

    # if touch_detection:
    #     if verbose_output: print("Touch detected! Stopping current speech and setting interruption flag.")
    #     nao.tts.request(
    #         NaoqiTextToSpeechRequest("Oh, I understand. Let me switch to a different time period in Amsterdam."))
    #     interrupted = True


nao.buttons.register_callback(test_func)

while True:
    pass  # Keep script alive
