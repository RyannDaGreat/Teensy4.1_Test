from urp import *

_config_cache={}

def get_config(*address):
	if address in _config_cache:
		return _config_cache[address]
	return file_to_object(path_join(*address))

def set_config(*address,value):
	return file_to_object(path_join(*address))

def Config:
	def __init__(self,)