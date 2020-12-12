# # CircuitPython demo - NeoPixel
# import time
# import board
# import neopixel

# pixel_pin = board.A1
# num_pixels = 119

# pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=.1, auto_write=False)


# def wheel(pos):
#     # Input a value 0 to 255 to get a color value.
#     # The colours are a transition r - g - b - back to r.
#     if pos < 0 or pos > 255:
#         return (0, 0, 0)
#     if pos < 85:
#         return (255 - pos * 3, pos * 3, 0)
#     if pos < 170:
#         pos -= 85
#         return (0, 255 - pos * 3, pos * 3)
#     pos -= 170
#     return (pos * 3, 0, 255 - pos * 3)


# def color_chase(color, wait):
#     for i in range(num_pixels):
#         pixels[i] = color
#         time.sleep(wait)
#         pixels.brightness=random()
#         pixels.show()
#     # time.sleep(0.5)

# from random import random

# import analogio
# from board import *
# adc=analogio.AnalogIn(A6)
# from time import sleep
# # for i in range(5000000):
# #     sleep(.0)
# #     print(adc.value/2**16)


# def pixel_height():
#     v=(adc.value/2**16)
#     print(v)
#     return int(v*num_pixels)


# def rainbow_cycle(wait):
#     for j in range(255):
#         pixels.fill((0,0,0))
#         for i in range(pixel_height()):
#             rc_index = (i * 256 // num_pixels) + j
#             pixels[i] = wheel(rc_index & 255)
#         # pixels.brightness=random()
#         pixels.show()
#         time.sleep(wait)


# RED = (255, 0, 0)
# YELLOW = (255, 150, 0)
# GREEN = (0, 255, 0)
# CYAN = (0, 255, 255)
# BLUE = (0, 0, 255)
# PURPLE = (180, 0, 255)


# from time import monotonic_ns
# def millis():
#     return monotonic_ns()//1000000
# def seconds():
#     return monotonic_ns() /1000000000
# _mtoc=millis()
# def mtic():
#     global _mtoc
#     now=millis()
#     out=now-_mtoc
#     _mtoc=now
#     return out
# def mtoc():
#     now=millis()
#     return now-_mtoc
# def mptoctic(*msg):
#     print(*(msg+('TOC:',mtoc(),'millis')))
#     mtic()


# def f():

#     print("GOGO ")
#     pixels.fill(RED)
#     pixels.show()
#     print("POD ")
#     # Increase or decrease to change the speed of the solid color change.
#     time.sleep(1)
#     mptoctic("Greenstart")
#     pixels.fill((255,255,255))
#     mptoctic("Greenend")
#     pixels.show()
#     time.sleep(5)
#     pixels.fill(BLUE)
#     print("sloggo ")
#     pixels.show()
#     time.sleep(1)

#     color_chase(RED, 0.00)  # Increase the number to slow down the color chase
#     color_chase(YELLOW, 0.000)
#     print("miranada ")
#     color_chase(GREEN, 0.00)
#     color_chase(CYAN, 0.00)
#     color_chase(BLUE, 0.00)
#     print("porky ")
#     color_chase(PURPLE, 0.00)

#     rainbow_cycle(0)  # Increase the number to slow down the rainbow
# # f()
# # pixels.brightness=
# # while True:
#     # rainbow_cycle(0)

# pixels.fill((0,0,0))
# # pixels.fill(RED)
# for i in range(100):
#     pixels.fill((0,0,0))
#     rainbow_cycle(0)