import board
import digitalio as dio

b1l = dio.DigitalInOut(board.D14)
b2l = dio.DigitalInOut(board.D15)
b3l = dio.DigitalInOut(board.D22)
b4l = dio.DigitalInOut(board.D23)
bmr = dio.DigitalInOut(board.D33)
bmb = dio.DigitalInOut(board.D36)
bmg = dio.DigitalInOut(board.D37)

bmr.switch_to_output()
bmb.switch_to_output()
bmg.switch_to_output()
b4l.switch_to_output()
b3l.switch_to_output()
b2l.switch_to_output()
b1l.switch_to_output()

b1o = dio.DigitalInOut(board.D39)
b2o = dio.DigitalInOut(board.D40)
b3o = dio.DigitalInOut(board.D41)
b4o = dio.DigitalInOut(board.D16)
bmo = dio.DigitalInOut(board.D38)

bmo.switch_to_input(pull=dio.Pull.UP)
b4o.switch_to_input(pull=dio.Pull.UP)
b3o.switch_to_input(pull=dio.Pull.UP)
b2o.switch_to_input(pull=dio.Pull.UP)
b1o.switch_to_input(pull=dio.Pull.UP)

class Button:
	pass

class GreenButton(Button):
	def __init__(self,read_io,light_io):
		assert isinstance(read_io ,dio.DigitalInOut)
		assert isinstance(light_io,dio.DigitalInOut)
		self.read_io =read_io
		self.light_io=light_io
	
	@property
	def value(self)->bool:
		return not self.read_io.value

	@property
	def light(self)->bool:
		return self.light_io.value

	@light.setter
	def light(self,value:bool):
		self.light_io.value=value


class MetalButton(Button):
	def __init__(self,read_io,red_io,green_io,blue_io):
		assert isinstance(read_io ,dio.DigitalInOut)
		assert isinstance(red_io  ,dio.DigitalInOut)
		assert isinstance(green_io,dio.DigitalInOut)
		assert isinstance(blue_io ,dio.DigitalInOut)
		self.read_io =read_io
		self.red_io=red_io
		self.green_io=green_io
		self.blue_io=blue_io

	@property
	def value(self):
		return self.read_io.value

	@property
	def red(self):
		return self.red_io.value
	
	@red.setter
	def red(self,value):
		self.red_io.value=value

	@property
	def green(self):
		return self.green_io.value

	@green.setter
	def green(self,value):
		self.green_io.value=value

	@property
	def blue(self):
		return self.blue_io.value

	@blue.setter
	def blue(self,value):
		self.blue_io.value=value

	@property
	def color(self):
		return (self.red,self.green,self.blue)

	@color.setter
	def color(self,value):
		assert len(value)==3
		r,g,b=value
		self.red=r
		self.green=g
		self.blue=b

green_button_1=GreenButton(b1o,b1l)
green_button_2=GreenButton(b2o,b2l)
green_button_3=GreenButton(b3o,b3l)
green_button_4=GreenButton(b4o,b4l)
green_buttons=(green_button_1,green_button_2,green_button_3,green_button_4)

def set_green_button_lights(l1,l2,l3,l4):
	green_button_1.light=l1
	green_button_2.light=l2
	green_button_3.light=l3
	green_button_4.light=l4

def get_green_button_lights():
	return (green_button_1.light,
	        green_button_2.light,
	        green_button_3.light,
	        green_button_4.light)

class TemporaryGreenButtonLights:
	#Meant to be used with the 'with' keyword
	#Temporarily sets the green buttons' lights 
	def __init__(self,l1=False,l2=False,l3=False,l4=False):
		self.l1=l1
		self.l2=l2
		self.l3=l3
		self.l4=l4
	def __enter__(self,*args):
		self.old_lights=get_green_button_lights()
		set_green_button_lights(self.l1,self.l2,self.l3,self.l4)
	def __exit__(self,*args):
		set_green_button_lights(*self.old_lights)

class TemporaryMetalButtonLights:
	#Meant to be used with the 'with' keyword
	#Temporarily sets the green metal button's rgb lights 
	def __init__(self,r,g,b):
		self.r=r
		self.g=g
		self.b=b
	def __enter__(self,*args):
		self.old_metal_color=metal_button.color
		metal_button.color=(self.r,self.g,self.b)
	def __exit__(self,*args):
		metal_button.color=self.old_metal_color


metal_button=MetalButton(bmo,bmr,bmg,bmb)

class ButtonPressViewer:
	def __init__(self,button:Button):
		self.button=button
		self.old_value=button.value

	@property
	def value(self):
		#Will appear to be True only once per stroke
		new_value=self.button.value
		if self.old_value!=new_value and new_value:
			out = True
		else:
			out = False
		self.old_value=new_value
		from time import sleep
		# sleep(.05)#This is a crude, sloppy way of debouncing the button...it's good enough for now lol
		return out
