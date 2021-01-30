#r stands for 'micro-rp'
#This library is originally designed for CircuitPython on my Teensy4.0 and Teensy4.1 boards. If using other implementations or boards, you might need to adapt this code.

#Attempt to make the Teensy's drive space writeable...
read_only=True
import lightboard.battery
if lightboard.battery.is_connected():
	import lightboard.display
	lightboard.display.set_text("BATTERY ON!")
	try:
		#Try to mitigate errors when saving files
		#		open('file.txt','wb')
		#	results in...
		#		OSError: [Errno 30] Read-only filesystem
		import storage
		storage.remount('/', readonly=False)
		read_only=False
		lightboard.display.set_text("Writeable!")
	except RuntimeError as error:
		#When plugged into USB, this doesn't work - and there's no way to write to the filesystem :\
		#SD cards don't work in the current circuitpython version...
		#	RuntimeError: Cannot remount '/' when USB is active.
		print("Failed to remount:",error)
		pass

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

def midi_note_off(note:int,vel:int=127,chan:int=0):
	assert 0<=note<128
	assert 0<=vel <128
	assert 0<=chan<16
	return bytes([0x80+chan,note,vel])

def midi_note_on(note:int,vel:int=127,chan:int=0):
	assert 0<=note<128
	assert 0<=vel <128
	assert 0<=chan<16
	return bytes([0x90+chan,note,vel])

def shuffle(array)->None:
	#Mutates an input list such that it's shuffled
	import random
	max_index=len(array)-1
	for index in range(max_index):
		random_index=random.randint(index,max_index)
		array[index],array[random_index] = array[random_index],array[index]

def shuffled(array):
	if isinstance(array,str  ):return ''.join(shuffled(list(array)))
	if isinstance(array,bytes):return bytes(shuffled(list(array))) #Maybe use a memory view to make it faster?
	array=array.copy()
	shuffle(array)
	return array

def save_object_via_umsgpack(object,path):
	import umsgpack
	data=umsgpack.packb(object)

def bytes_to_file(data:bytes,path:str=None):
	assert not read_only,'Filesystem is read-only - make sure CircuitPython isnt connected to a computer via USB'
	assert isinstance(data,bytes)
	assert isinstance(path,str)
	try:
		out=open(path,'wb')
		out.write(data)
	finally:
		out.close()

def file_to_bytes(path:str):
	try:
		out=open(path,'rb')
		data=out.read()
	finally:
		out.close()
	return data

def bytes_to_object(data:bytes):
	import umsgpack
	return umsgpack.unpackb(data)

def object_to_bytes(object):
	import umsgpack
	return umsgpack.packb(object)

def file_to_object(path:str):
	return bytes_to_object(file_to_bytes(path))

def object_to_file(object,path:str):
	return bytes_to_file(object_to_bytes(object),path)

def path_exists(path:str):
	import os
	try:
		os.stat(path)
		return True
	except OSError:
		#OSError: [Errno 2] No such file/directory
		return False


