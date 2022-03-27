import board
import busio
from urp import *
from linear_modules import *
import lightboard.display as display
import lightboard.buttons as buttons
import lightboard.pressure as pressure
import lightboard.widgets as widgets
import lightboard.ribbons as ribbons #Shouldn't cause errors. No scl/sda pullup means the board isn't connected. No i2c at 48 means the individual chip isn't powered or connected etc. I just ficed a bad solder joint that took a while to flare up.......maybe this is what happened with the old lightwave? I was too quick with the solder joints, leaving a bubble that didn't touch it because of some stress bs later on?


ribbons.test_ribbon_raw_uart(ribbons.ribbon_a)



if not widgets.input_yes_no('Connected to PC?'):
	attempt_to_mount()


# pressure.test_pressure()

pressure.show_calibration_menu()