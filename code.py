import board
import busio
from urp import *
from linear_modules import *
import lightboard.display as display
import lightboard.buttons as buttons
import lightboard.pressure as pressure
import lightboard.widgets as widgets
import lightboard.ribbons as ribbons

if not widgets.input_yes_no('Connected to PC?'):
	attempt_to_mount()

# ribbons.ribbon_a.run_calibration()
ribbons.show_calibration_menu()
pressure.show_calibration_menu()
