#!/usr/bin/python
from bitstring import BitArray
from collections import deque
from sys import argv

# games
earlier_games = ['Maelstrom','Chiral','Apeiron','Swoop','Barrack','Escape Velocity','Avara','Bubble Trouble','Harry']
later_games = ['Mars Rising','EV Override','Slithereens','Cythera','Ares']

def rotate(bits,num):
	b = deque(bits)
	b.rotate(num)
	return BitArray(b)

def add(a,b):
	return BitArray('0b' + format(a + b,'032b'))

def hash_code(string,number,code,extra_hash=False):
	for i in range(0,len(string)):

		code[24:] = add(ord(string[i]),int(code[24:].hex,16))[24:] # add current letter

		if extra_hash:
			code = rotate(code,-6) # rotate left 6
			code[16:] = add(number,int(code[16:].hex,16))[16:] # add number copies
			code = code ^ BitArray('0xDEADBEEF') # xor with key
			code = rotate(code,1) # rotate right 1

		else: # earlier games don't seem to include XOR with $DEADBEEF
			code = rotate(code,-5) # rotate left 5
			code[16:] = add(number,int(code[16:].hex,16))[16:] # add number copies

	return code

def generate_code(name,number,game):
	code = BitArray(32) # 4-byte code of 0's to process on
	name = name.upper() # name uppercase only

	code = hash_code(name,number,code,game in later_games)
	code = hash_code(game,number,code,game in later_games)

	registration = '' # ASCII string for registration code
	for i in range(8):
		code = rotate(code,-4) # rotate left 4
		# for each LSB nibble, add ASCII offset (first 16 letters only)
		registration += chr(int(code[28:].hex,16)+65)

	return registration[::-1] # reverse


if __name__ == '__main__':
	try:
		if len(argv) > 4:
			raise
		print(generate_code(argv[1],int(argv[2]),argv[3]))
	except:
		print('Usage: "<name>" <number> "<game>"')
