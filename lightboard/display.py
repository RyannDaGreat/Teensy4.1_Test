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

WIDTH=const(320)
HEIGHT=const(240)

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D6)

display = ST7789(display_bus, width=WIDTH, height=HEIGHT, rotation=90)

# Make the display context
splash = displayio.Group(max_size=10)
display.show(splash)

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x0000FF  # Bright Blue

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
BORDER_THICKNESS=const(10)
inner_bitmap = displayio.Bitmap(WIDTH-BORDER_THICKNESS*2, HEIGHT-BORDER_THICKNESS*2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER_THICKNESS, y=BORDER_THICKNESS)
splash.append(inner_sprite)

# Draw a label
text_group = displayio.Group(max_size=10, scale=1, x=25, y=25)
text = "Hello World!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF,max_glyphs=512)
text_group.append(text_area)  # Subgroup for text scaling
splash.append(text_group)

#INTERFACE IS SUBJECT TO MAJOR CHANGES SOON
def set_text(text:str):
	text_area.text=text
	display.refresh()

class TemporarySetText:
	def __init__(self,text):
		self.text=text
	def __enter__(self):
		self.old_text=text_area.text
		text_area.text=self.text
	def __exit__(self,*args):
		text_area.text=self.old_text

