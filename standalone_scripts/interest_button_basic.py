from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

def test_func(event):
    sensor = event.value
    print(f"sensor info 0: {sensor[0]}")
    print(f"sensor info 1: {sensor[1]}")

    print(event.value)

    touch_detection = any(sensor_info[1] == True for sensor_info in sensor)

    if touch_detection:
        nao.tts.request(NaoqiTextToSpeechRequest("Oh, I understand you would like to change the topic. How about we talk about the twenties?"))


nao = Nao(ip="10.0.0.198")

nao.buttons.register_callback(test_func)
