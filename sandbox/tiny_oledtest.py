#This is meant for the small led

from time import monotonic_ns
def millis():
	return monotonic_ns()//1000000

def seconds():
	return monotonic_ns() /1000000000

import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

displayio.release_displays()

oled_reset = board.D9

# Use for I2C
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C, reset=oled_reset)

# Use for SPI
# spi = board.SPI()
# oled_cs = board.D5
# oled_dc = board.D6
# display_bus = displayio.FourWire(spi, command=oled_dc, chip_select=oled_cs,
#                                 reset=oled_reset, baudrate=1000000)

WIDTH = 128
HEIGHT = 32  # Change to 64 if needed
BORDER = 5

display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)


def f(text='Hello World!'):
	# Make the display context
	splash = displayio.Group()

	color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
	color_palette = displayio.Palette(1)
	color_palette[0] = 0xFFFFFF  # White

	bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
	splash.append(bg_sprite)
	# Draw a smaller inner rectangle
	inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
	inner_palette = displayio.Palette(1)
	inner_palette[0] = 0x000000  # Black
	inner_sprite = displayio.TileGrid(
	    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
	)
	splash.append(inner_sprite)

	# Draw a label
	# text = "Hello World!"
	text_area = label.Label(
	    terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1
	)
	splash.append(text_area)
	display.show(splash)
f()

# for i in range(10000):
while True:
	# f("Hello")
	s=seconds()
	# sleep(1/60)
	from time import sleep
	f(str(s))
	e=seconds()-s
	sleep(1/60)
