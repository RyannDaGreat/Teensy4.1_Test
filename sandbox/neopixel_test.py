import board
import neopixel_write
import digitalio

pin = digitalio.DigitalInOut(board.D30)
pin.direction = digitalio.Direction.OUTPUT
pixel_off = bytearray([255, 128, 255]*10)
neopixel_write.neopixel_write(pin, pixel_off)