import board
import busio
from urp import *
from linear_modules import *
import lightboard.display as display
import lightboard.buttons as buttons
import lightboard.pressure as pressure
import lightboard.widgets as widgets


if not widgets.input_yes_no('Connected to PC?'):
	attempt_to_mount()


pressure.test_pressure()

pressure.show_calibration_menu()