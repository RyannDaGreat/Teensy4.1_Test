from urp import *
import time
import struct
import board
import digitalio as dio
from time import sleep

from circuitpython_nrf24l01.rf24 import RF24

spi = board.SPI()  # init spi bus object

ce = dio.DigitalInOut(board.D21)
csn = dio.DigitalInOut(board.D20)
nrf = RF24(spi, csn, ce)

assert False,'GOODIVA - we havent tried setting up the second yet.'


nrfB = RF24(spi, csn, ce)
nrf.dynamic_payloads = False  # the default in the TMRh20 arduino library
nrfB.dynamic_payloads = False  # the default in the TMRh20 arduino library

# set the Power Amplifier level to -12 dBm since this test example is
# usually run with nRF24L01 transceivers in close proximity
nrf.pa_level = -12

# change this variable to oppose the corresponding variable in the
# TMRh20 library's GettingStarted_HandlingData.ino example
radioNumber = True

ce2 = dio.DigitalInOut(board.D41)
csn2 = dio.DigitalInOut(board.D8)
nrf2 = RF24(spi, csn2, ce2)
nrf2B = RF24(spi, csn2, ce2)
nrf2.dynamic_payloads = False  # the default in the TMRh20 arduino library
nrf2B.dynamic_payloads = False  # the default in the TMRh20 arduino library

nrf .open_rx_pipe(pipe_number=1, address=b'a')
nrf .open_tx_pipe(               address=b'a')

nrf2.open_rx_pipe(pipe_number=1, address=b'a')
nrf2.open_tx_pipe(               address=b'a')

nrfB .open_rx_pipe(pipe_number=2, address=b'rx')
nrfB .open_tx_pipe(               address=b'tx')

nrf2B.open_rx_pipe(pipe_number=2, address=b'rx')
nrf2B.open_tx_pipe(               address=b'tx')


print("\n\nPART 1")
nrf.listen=False
nrf2.listen=True
nrf.write(b"Hello World!") #the .write function is like UDP and the .send function is like TCP (it's blocking)
print(nrf2.recv(32))

print("\n\nPART 2")
nrf.listen=True
nrf2.listen=False
tic()
nrf2.write(b"1...............................")
nrf2.write(b"2...............................")
nrf2.write(b"3...............................")
nrf2.write(b"4...............................")
nrf2.write(b"5...............................")
nrf2.write(b"6...............................")
nrf2.write(b"7...............................")
nrf2.write(b"8...............................")
nrf2.write(b"9...............................")
ptoctic()
print(nrf.recv(32*79))
ptoc()


#I need some way to do this...
print("\n\nPART 3")
nrf.listen=nrf2.listen=False
nrfB.listen=nrf2B.listen=True
# nrf.listen=nrf2.listen=False
nrf .write(b"Hello World! From nrf") #the .write function is like UDP and the .send function is like TCP (it's blocking)
nrf2.write(b"Hello World! From nrf2") #the .write function is like UDP and the .send function is like TCP (it's blocking)

print(nrfB.recv(32))
print(nrf2B.recv(32))
