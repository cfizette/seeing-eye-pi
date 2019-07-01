# Runs in background and launches camera app when button pressed.
# Should be setup to run when Pi is booted.
from buttons import GPIOButton
import subprocess
launch_button = GPIOButton(22)
while True:
    if launch_button.is_pressed():
        subprocess.call(['python', 'cam.py'])