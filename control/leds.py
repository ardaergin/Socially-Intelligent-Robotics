from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest

class LEDControl:
    def __init__(self, nao):
        self.nao = nao
    
    def set_eye_color(self, color):
        colors = {'green': (0, 1, 0, 0), 'blue': (0, 0, 1, 0), 'off': (0, 0, 0, 0)}
        self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", *colors[color]))
