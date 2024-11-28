def register_touch_callback(nao, interrupt_handler):
    """
    Register the touch callback for the NAO robot.

    :param nao: The NAO robot instance.
    :param interrupt_handler: A function to call when a touch interrupt occurs.
    """
    def touch_stop(event):
        """
        Callback function for handling touch events.

        :param event: The touch event data.
        """
        sensor = event.value
        print("Sensor info:", sensor)
        if any(sensor_info[1] for sensor_info in sensor):
            print("Touch detected! Interrupting...")
            interrupt_handler(True)

    # Register the callback
    nao.buttons.register_callback(touch_stop)
