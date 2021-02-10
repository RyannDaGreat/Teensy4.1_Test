import lightboard.buttons as buttons
from urp import *

def input_yes_no(prompt):
	import lightboard.display as display
	with buttons.TemporaryGreenButtonLights(1,0,0,0):
		with buttons.TemporaryMetalButtonLights(1,0,0):
			# with display.TemporarySetText(prompt+'\n(Button 1 -> Yes, Metal Button -> No)'):
				display.set_text(prompt+'\n(Button 1 -> Yes, Metal Button -> No)')
				while True:
					if buttons.metal_press_viewer.value:
						return False
					elif buttons.green_1_press_viewer.value:
						return True

def input_select(options,prompt='Please select an option:',can_cancel=False,must_confirm=True):
	import lightboard.buttons as buttons
	import lightboard.display as display

	prompt_lines=prompt.split('\n')
	prefix=prompt_lines+['Green: 1,2 -> Up/Down, 3 -> Select']
	if can_cancel:
		prefix+=['Metal: Cancel']
	prefix+=['']
	
	colors=[0x88FF88]*len(prompt_lines)+[0x448888,0x448888]

	index=0
	with buttons.TemporaryGreenButtonLights(1,1,1,0):
		with buttons.TemporaryMetalButtonLights(1,0,1) if can_cancel else buttons.TemporaryMetalButtonLights(0,0,0):
			while True:
				if buttons.green_1_press_viewer.value:
					index-=1
				if buttons.green_2_press_viewer.value:
					index+=1
				if buttons.green_3_press_viewer.value:
					if not must_confirm or input_yes_no("Are you sure you want to select\n    "+repr(options[index])):
						return options[index]
				if buttons.metal_press_viewer.value and can_cancel and input_yes_no("Are you sure you want to cancel?"):
					raise KeyboardInterrupt

				index%=len(options)
				display.set_menu(labels=prefix+options,index=len(prefix)+index,colors=colors)
