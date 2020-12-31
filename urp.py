#r stands for 'micro-rp'
#This library is originally designed for CircuitPython on my Teensy4.0 and Teensy4.1 boards. If using other implementations or boards, you might need to adapt this code.


from time import monotonic_ns
def millis():
	return monotonic_ns()//1000000

def seconds():
	return monotonic_ns() /1000000000

_toc=0
def gtoc():
	return seconds()
def toc():
	return gtoc()-_toc
def tic():
	global _toc
	_toc=gtoc()
def ptoc(*args):
	print(*(args+('%.7f'%toc(),)))
def ptoctic(*args):
	ptoc(*args)
	tic()

def clamp(x,a,b):
	return min(max(a,b),max(min(a,b),x))
