#urp stands for 'micro-rp'
#This library is originally designed for CircuitPython on my Teensy4.0 and Teensy4.1 boards. If using other implementations or boards, you might need to adapt this code.


from time import monotonic_ns
def millis():
	return monotonic_ns()//1000000

def seconds():
	return monotonic_ns() /1000000000

