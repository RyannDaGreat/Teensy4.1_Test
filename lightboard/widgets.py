import lightboard.buttons as buttons
import lightboard.display as display
def input_yes_no(prompt):
	with buttons.TemporaryGreenButtonLights(1,0,0,0):
		with buttons.TemporaryMetalButtonLights(1,0,0):
			with display.TemporarySetText(prompt+'\n(Button 1 -> Yes, Metal Button -> No)'):
				metal_presses=buttons.ButtonPressViewer(buttons.metal_button)
				green_presses=buttons.ButtonPressViewer(buttons.green_button_1)
				while True:
					if metal_presses.value:
						return False
					elif green_presses.value:
						return True