#r stands for 'micro-rp'
#This library is originally designed for CircuitPython on my Teensy4.0 and Teensy4.1 boards. If using other implementations or boards, you might need to adapt this code.
#Attempt to make the Teensy's drive space writeable...
read_only=True
import lightboard.battery
if lightboard.battery.is_connected():
	# import lightboard.display
	# lightboard.display.set_text("BATTERY ON!")
	try:
		#Try to mitigate errors when saving files
		#		open('file.txt','wb')
		#	results in...
		#		OSError: [Errno 30] Read-only filesystem
		import storage
		storage.remount('/', readonly=False)
		read_only=False
		# lightboard.display.set_text("Writeable!")
	except RuntimeError as error:
		#When plugged into USB, this doesn't work - and there's no way to write to the filesystem :\
		#SD cards don't work in the current circuitpython version...
		#	RuntimeError: Cannot remount '/' when USB is active.
		print("Failed to remount:",error)
		pass

from time import monotonic_ns
from micropython import const

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

def midi_all_notes_off():
	return bytes([123,0])

def midi_all_sound_off():
	return bytes([121,0])

def midi_volume(vol:int):
	assert 0<=vol<256
	return bytes([3,vol])

def midi_note_on(note:int,vel:int=127,chan:int=0):
	assert 0<=note<128
	assert 0<=vel <128
	assert 0<=chan<16
	return bytes([0x90+chan,note,vel])

def midi_pitch_bend(coarse:int,fine:int):
	return bytes([224,coarse,fine])

def midi_pitch_bend_from_semitones(semitones,lower=-2,upper=2):
	value=(semitones-lower)/(upper-lower)
	coarse=int(value*128)
	fine=int(value*128**2)%128
	return midi_pitch_bend(clamp(fine,0,255),clamp(coarse,0,255))

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

def _path_join(path_a:str,path_b:str):
	#Joins paths together.
	#	EXAMPLES:
	#		path_join('folder' , 'file') --> 'folder/file'
	#		path_join('folder/', 'file') --> 'folder/file'
	#		path_join('folder/','/file') --> 'folder/file'
	#		path_join('folder ','/file') --> 'folder/file'
	if path_a.endswith('/'):
		path_a=path_a[:-1]
	if path_b.startswith('/'):
		path_b=path_b[1:]
	return path_a+'/'+path_b

def path_join(*paths):
	if not len(paths):
		return ''
	if len(paths)==1:
		return paths[0]
	output=paths[0]
	for path in paths[1:]:
		output=_path_join(output,path)
	return output

class EmptyContext:
	def __enter__(self,*args):
		pass
	def __exit__(self,*args):
		pass

def median(values):
	values=sorted(values)
	length=len(values)
	assert length>0,'Cannot get median of empty list'
	if length%2:
		return  values[length//2]
	else:
		return (values[length//2]+values[length//2-1])/2

def mean(l):
	l=list(l)
	return sum(l)/len(l)

def std(l):
	u=mean(l)
	return mean((x-u)**2 for x in l)**.5


def blend(x,y,a):
	return a*y+(1-a)*x
	
def interp(x,*y):
	x=max(0,min(x,len(y)-1))
	if x==int(x):
		return y[int(x)]
	return blend(y[int(x)],y[int(x)+1],x-int(x))

def note_to_pitch(note,*scale):
	#Usually scale will have length 12
	#Scale should be monotonically increasing
	return interp(note%(len(scale)-1),*scale)+scale[-1]*(note//(len(scale)-1))
	
major_scale=[0,2,4,5,7,9,11,12]
natural_minor_scale=[0,2,3,5,7,8,10,12]
harmonic_minor_scale=[0,2,3,5,7,8,11,12]
blues_scale=[0,3,5,6,7,10,12]
chromatic_scale=[0,1,2,3,4,5,6,7,8,9,10,11,12]

