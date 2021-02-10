import lightboard.buttons as buttons
from lightboard.config import config
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

def input_select(options,prompt='Please select an option:',can_cancel=False,must_confirm=True,num_options_per_page=13):
	import lightboard.buttons as buttons
	import lightboard.display as display

	prompt_lines=prompt.split('\n')
	prefix=prompt_lines+['Green: 1,2 -> Up/Down, 3 -> Select']
	if can_cancel:
		prefix+=['Metal: Cancel']
	
	colors=[0x88FF88]*len(prompt_lines)+[0x448888]*2

	page_num=0
	num_pages=len(options)//num_options_per_page
	prefix_page_num_index=None
	def update_prefix_page_num():
		prefix[prefix_page_num_index]='Showing page %i of %i'%(page_num,num_pages)
	if num_pages>0:
		colors+=[0xBB8844]
		prefix_page_num_index=len(prefix)
		prefix+=[None]#Will be updated by update_prefix_page_num
		update_prefix_page_num()
	options_offset=0

	prefix+=['']

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
				page_num=index//num_options_per_page
				options_offset=page_num*num_options_per_page
				visible_options=options[options_offset:options_offset+num_options_per_page]

				update_prefix_page_num()
				display.set_menu(labels=prefix+visible_options,
				                 index =len(prefix)+index%num_options_per_page,
				                 colors=colors)

def edit_config_int(address,min_value=None,max_value=None,default=0):
	#TODO: Create input_int and use that in edit_config_int (refactoring)
	if address not in config:
		config[address]=default
	
	original_value=config[address]
	value=original_value

	with buttons.TemporaryGreenButtonLights(1,1,1,0):
		with buttons.TemporaryMetalButtonLights(1,0,1):
			def update_display():
				display.set_menu(labels=['Editing '+address,
				                         'Int between %i and %i'%(min_value,max_value),
				                         '    Green 1 -> -1',
				                         '    Green 2 -> +1',
				                         '    Green 3 -> Done',
				                         '    Metal -> Cancel',
				                         '',
				                         address+' = '+str(value),
				                         ],
				                 colors=[0xFFFFFF,
				                         0xFFFFFF,
				                         0x00FF00,
				                         0x00FF00,
				                         0x00FF00,
				                         0xFF00FF,
				                         ]
				                )
			while True:
				buttons.green_button_1.light=value!=min_value
				buttons.green_button_1.light=value!=max_value
				
				if buttons.green_1_press_viewer.value:
					value-=1
					if min_value is not None:
						value=max(min_value,value)

				if buttons.green_2_press_viewer.value:
					value+=1
					if max_value is not None:
						value=min(max_value,value)

				if buttons.green_3_press_viewer.value:
					if input_yes_no("Are you sure you want to change\n%s from (old) %i to %i (new)?"%(address,original_value,config[address])):
						config[address]=value
						set_text('Confirmed: set %s to %i'%(address,config[address]))
						return

				if buttons.metal_press_viewer.value:
					if input_yes_no("Are you sure you want to cancel\n and keep %s as %i?"%(address,original_value)):
						config[address]=original_value
						return

				update_display()






