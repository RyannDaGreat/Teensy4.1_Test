class HistogramFitter:
	def __init__(self,bin_size):
		self.bin_size=bin_size
		self.histogram_sums={}
		self.histogram_freqs={}
		self._verified=False
		
	def add_sample(self,x,y):
		x/=self.bin_size
		x=int(x)
		if x not in self.histogram_sums:
			self.histogram_sums[x]=0
		if x not in self.histogram_freqs:
			self.histogram_freqs[x]=0
		self.histogram_freqs[x]+=1
		self.histogram_sums[x]+=y
		self._verified=False
		
	def __getitem__(self,x):
		self.verify()
		if   x>self.max_bin: x=self.max_bin
		elif x<self.min_bin: x=self.min_bin
		return self.histogram_sums[x]/self.histogram_freqs[x]
	
	def verify(self):
		if self._verified==True:
			#Don't waste time
			return
		
		#Internal assertion
		assert set(self.histogram_sums)==set(self.histogram_freqs)
		
		#Fill in any holes in the histogram
		min_bin=min(self.histogram_sums)
		max_bin=max(self.histogram_sums)
		self.max_bin=max_bin
		self.min_bin=min_bin
		prev_freq=self.histogram_freqs[min_bin]
		prev_sum =self.histogram_sums [min_bin]
		for i in range(min_bin,max_bin+1):
			#Todo: Add linear interpolation instead of the simple step function used here
			if i not in self.histogram_sums:
				self.histogram_sums[i]=prev_sum
				assert i not in self.histogram_freqs
				self.histogram_freqs[i]=prev_freq
				
			prev_freq=self.histogram_freqs[i]
			prev_sum =self.histogram_sums [i]
			
		self._verified=True
	
	def __call__(self,x):
		x/=self.bin_size
		x-=1/2 #Correct the placement of the bins
		if x==int(x):
			return self[int(x)]
		alpha=x-int(x)
		return self[int(x)]+alpha*(self[int(x)+1]-self[int(x)])

class NeopixelRibbonVoltageCalibrator:
	def __init__(self,reader,gate):
		#This object is meant to fit a raw analog input to the voltage drops caused by neopixels
		#As it turns out, from many experiments, the voltage drop proportion is a function to the sum of all the color values in the neopixel strip
		#    (This assumption might not hold for other neopixel strips; but with this one, red green and blue all have the same effect on the ribbon's voltage drop)
		#    (Also, the analog input drop on the ribbon is proportional to the value of the ribbon when all lights are off, assuming the user is pressing on it)
		#TODO: Create a way to save and load calibrations
		self.fit=HistogramFitter(50)
		assert callable(reader),'reader is supposed to be a function that returns a numerical value'
		assert callable(gate),'gate is supposed to be a function that returns a boolean value indicating if the ribbon is being pressed'
		self.reader=reader
		self.gate=gate

	def calibrate(self,num_samples=2000):
		#When this is calibrating, please move your finger along the ribbon...
		#Keep doing that until the lights stop flashing...

		while not self.gate():
			pass

		for _ in range(num_samples):

			random_partitions=random_partition(numpix*3,3)
			random_colors=bytearray([  0]*random_partitions[0]
			                       +[127]*random_partitions[1]
			                       +[255]*random_partitions[2])
			shuffle(random_colors)

			progress_pixel=int(numpix*(_/num_samples))
			random_colors[progress_pixel*3+0]=0
			random_colors[progress_pixel*3+1]=0
			random_colors[progress_pixel*3+2]=0

			write_to_neopixels(pixel_off)
			originalval=self.reader()
			write_to_neopixels(random_colors)
			newval=self.reader()

			factor=originalval/newval

			x=sum(random_colors)
			x=ads_a_single.value
			y=math.log(factor)

			#Print out the results so we can plot them in desmos
			print('%i , %.9f'%(x,y))

			self.fit.add_sample(x,y)

	def __call__(self):
		return self.reader()*math.exp(self.fit(sum(neopixel_data)))