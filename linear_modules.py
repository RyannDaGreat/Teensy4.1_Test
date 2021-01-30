class Squelcher:
	def __init__(self,callable,value=None,error=None,exception_class=Exception):
		#Interfaces like a linear module but can take more than just number classes
		self.callable=callable
		self.error=error
		self.value=value
		self.exception_class=exception_class
	def __call__(self):
		self.error=None
		try:
			self.value=self.callable()
		except self.exception_class as error:
			self.error=error
		return self.value

#These LinearModule-like classes are all callable when inputting a new value, and all store a 'value' parameter to get the last calulated value 
#It's supposed to be pythonic; as opposed to jWave (which implicitly creates a tree). This is more like pytorch than tensorflow...let's see how it goes. 
class Tether:
	def __init__(self,size=1,value=None):
		self.size=size
		self.value=value
	def __call__(self,value):
		if self.value is None:
			self.value=value
		else:
			self.value=clamp(self.value,value-self.size,value+self.size)
		return self.value

class SoftTether:
	#Acts similar to Tether, but has nicer properties (is smoother, and large jumps cause near-perfect centering for example)
	def __init__(self,size=1,value=None):
		self.size=size
		self.value=value
	def __call__(self,value):
		if self.value is None:
			self.value=value
		else:
			alpha=1-2.718**(-((value-self.value)/self.size)**2)
			self.value=alpha*value+(1-alpha)*self.value
		return self.value

class Legato:
	def __init__(self,alpha,value=None):
		self.value=value
		self.alpha=alpha
	def __call__(self,value):
		if self.value is None:
			self.value=value
		else:
			self.value=self.alpha*value+self.value*(1-self.alpha)
		return self.value

class Differential:
	#TODO: Make a version of this class that takes time into account?
	def __init__(self,prev=None,value=None):
		self.prev=prev
		self.value=value
	def __call__(self,value):
		if self.value is None:
			self.prev=value
		self.value=value-self.prev
		self.prev=value
		return self.value

class MovingAverage:
	def __init__(self,length:int):
		#A moving average with 'length' number of samples
		#Todo: To save memory, make a general-purpose sliding window class so that MovingAverage's window can be shared with Delay's window can be shared with MovingMedian's window
		#Todo: Dynamically adjustable length
		assert length>0,'Must have a positive length'
		self.values=[0]*length
		self._length=length
		self._total=0
		self._count=0
		self._cursor=0

	def __call__(self,value):
		self._count=min(self._length,self._count+1)
		self._cursor%=self._length
		self._total-=self.values[self._cursor]
		self.values[self._cursor]=value
		self._total+=value
		self._cursor+=1
		self.value=self._total/self._count
		return self.value

def median(values):
	values=sorted(values)
	length=len(values)
	assert length>0,'Cannot get median of empty list'
	if length%2:
		return  values[length//2]
	else:
		return (values[length//2]+values[length//2-1])/2

class MovingMedian:
	#TODO: Make this more efficient; perhaps use ulab?
	def __init__(self,length):
		assert length>0,'Must have a positive length'
		self.length=length
		self.values=[]
	def __call__(self,value):
		self.values.append(value)
		self.values=self.values[-self.length:]
		self.value=median(self.values)
		return self.value
