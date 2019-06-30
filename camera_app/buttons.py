import RPi.GPIO as GPIO

class GPIOButton(object):
    def _init__(self, pin, pull_up_down=GPIO.PUD_UP):
        self.pin = pin
        self.pull_up_down = pull_up_down
        GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
        '''
        If pin is set with a pull_up resistor, then its unpressed state is True
        If pin is set with a pull down resistor, then its unpressed state is False
        Need to configure button to correctly detect when button is pressed
        '''
        if pull_up_down == GPIO.PUD_UP:
            self.pressed_val = False
        else:
            self.pressed_val = True

    def is_pressed(self):
        button_state = GPIO.input(self.pin)
        if button_state == self.pressed_val:
            return True
        return False
