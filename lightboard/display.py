"""
This test will initialize the display using displayio and draw a solid green
background, a smaller purple rectangle, and some yellow text.
"""
import board
import terminalio
import displayio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
from micropython import const

import digitalio

led = digitalio.DigitalInOut(board.D5)
led.switch_to_output()
led.value=True

# Release any resources currently in use for the displays
displayio.release_displays()

spi = board.SPI()
tft_cs = board.D10
tft_dc = board.D9

ROTATION=0#0,90,180,270
WIDTH=320
HEIGHT=240
if not ROTATION%180:
	HEIGHT,WIDTH=WIDTH,HEIGHT

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D6)

display = ST7789(display_bus, width=WIDTH, height=HEIGHT, rotation=0)

# Make the display context
text_splash = displayio.Group(max_size=64)
display.show(text_splash)

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x0000FF  # Bright Blue

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
text_splash.append(bg_sprite)

# Draw a smaller inner rectangle
BORDER_THICKNESS=const(10)
inner_bitmap = displayio.Bitmap(WIDTH-BORDER_THICKNESS*2, HEIGHT-BORDER_THICKNESS*2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER_THICKNESS, y=BORDER_THICKNESS)
text_splash.append(inner_sprite)

# Draw a label
text_group = displayio.Group(max_size=1, scale=1, x=25, y=25)
text = "Hello World!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF,max_glyphs=1024)#512 is probably good enough for most purposes...but 1024 can fill the entire screen AND more...512 cannot...1024 takes about 4kb more memory than 512.
text_group.append(text_area)  # Subgroup for text scaling
text_splash.append(text_group)

# text_area2 = label.Label(terminalio.FONT, text="GRUMBO", y=25, color=0xFFFFFF,max_glyphs=1024)#512 is probably good enough for most purposes...but 1024 can fill the entire screen AND more...512 cannot...1024 takes about 4kb more memory than 512.
# text_splash.append(text_area2)  # Subgroup for text scaling
menu_splash = displayio.Group(max_size=60)
MENU_MAX_LINES=30
MENU_LINE_SPACING=10
MENU_MAX_CHARS_PER_LINE=60
MENU_X_ORIGIN=25
MENU_Y_ORIGIN=25
menu_labels=[]
for i in range(MENU_MAX_LINES):
	menu_label = label.Label(terminalio.FONT,text='Line %i TEST Text ---___---'%i, color=0xFFFFFF,max_glyphs=MENU_MAX_CHARS_PER_LINE,x=MENU_X_ORIGIN, y=MENU_Y_ORIGIN+i*MENU_LINE_SPACING)
	menu_splash.append(menu_label)
	menu_labels.append(menu_label)
	display.refresh()


display_mode='text' #text, menu

#INTERFACE IS SUBJECT TO MAJOR CHANGES SOON
def set_text(text:str,refresh=True):
	global display_mode
	if display_mode!='text':
		displayio.release_displays()
		display.show(text_splash)
		display_mode='text'
	text_area.text=text
	if refresh:
		display.refresh()

class TemporarySetText:
	def __init__(self,text):
		self.text=text
	def __enter__(self):
		self.old_text=text_area.text
		set_text(self.text,refresh=False)
	def __exit__(self,*args):
		set_text(self.old_text,refresh=False)

######################### EFFICIENT MENU DISPLAYS ############################

# Make the display context
# menu_splash = text_splash#displayio.Group(max_size=20)

# MENU_MAX_LINES=12
# MENU_LINE_SPACING=10
# MENU_MAX_CHARS_PER_LINE=60
# MENU_X_ORIGIN=25
# MENU_Y_ORIGIN=25
# menu_labels=[]
# for i in range(MENU_MAX_LINES):
# 	print("SHOWING",i)
# 	menu_label = label.Label(terminalio.FONT,text='Line %i TEST Text ---___---'%i, color=0xFFFFFF,max_glyphs=MENU_MAX_CHARS_PER_LINE,x=MENU_X_ORIGIN, y=MENU_Y_ORIGIN+i*MENU_LINE_SPACING)
# 	# menu_labels.append(menu_label)
# 	menu_splash.append(menu_label)
# 	display.refresh()


# while True:pass

def set_menu(labels,colors=None,refresh=True):
	assert len(labels)<=MENU_MAX_LINES
	labels=tuple(labels)
	if colors is None:
		colors=tuple(menu_label.color for menu_label in menu_labels)
	global display_mode
	if display_mode!='menu':
		displayio.release_displays()
		display.show(menu_splash)
		display_mode='menu'
	for label in labels:
		assert isinstance(label,str)
		assert '\n' not in label,'Menu labels can only be one line. Anything else is too ugly to bear...'
	for i,label in enumerate(labels+('',)*(len(menu_labels)-len(labels))):
		print(i,len(menu_labels),len(labels),'CHUNKER')
		color=colors[i]
		if menu_labels[i].text!=label:
			#Only change the ones that need to be changed...
			menu_labels[i].text=label
		if menu_labels[i].color!=color:
			menu_labels[i].color=color

	if refresh:
		display.refresh()

display.refresh()

def lines(i=0):
	w=30
	h=MENU_MAX_LINES-1
	lines=[('-' if i%2 else '-')*w]*h
	lines.insert(i,'i'*w)
	return '\n'.join(lines)


# while True:
# 	for i in range(3):
# 		print(i,'CHUMP')
# 		set_text(lines(i))

while True:
	for i in range(MENU_MAX_LINES):
		print(i)
		colors=[0xFFFFFF]*MENU_MAX_LINES
		colors[i]=0xFF00FF
		set_menu(lines(i).split('\n'),colors)
		# display.refresh()


def set_menu_options(selected_index,prompt,options):
	pass




