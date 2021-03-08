#!/usr/bin/python
from bitstring import BitArray
from sys import argv

import aswreg_v2core as core


def textcode_to_bincode(textcode):
	textcode = textcode.upper()
	if len(textcode.replace('-','')) > 12:
		return

	# no 0,1,O,I -- causes confusion, plus this amount allows for 5-bit indexing (32 values)
	ref = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
	r30 = BitArray(32)
	r29 = BitArray(32)

	for i in range(0,len(textcode)):
		if (textcode[i] == '-'):
			continue
		r5 = BitArray('0b' + format(ref.index(textcode[i]),'032b'))
		r3 = r30 << 5
		r4 = r29 << 5
		r3[27:32] ^= r29[0:5]
		r0 = r5 >> 31
		r29 = r4 | r5
		r30 = r3 | r0

	return r30 + r29

def bincode_to_textcode(bincode):
	ref = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
	textcode = ''

	for i in range(4,64,5):
		textcode += ref[int(bincode[i:i+5].bin,2)]
		if i == 19 or i == 39:
			textcode += '-'

	return textcode


def date_code(code,name,number,game,decade=0):
	bincode = textcode_to_bincode(code)
	hash1 = core.get_hash1(name,number,game)
	hash2 = bincode ^ hash1
	return core.timestamp_to_datetime(core.get_hash2_time(hash2),decade)


def renew_code(code,name,number,game):
	bincode = textcode_to_bincode(code)
	hash1 = core.get_hash1(name,number,game)
	hash2 = bincode ^ hash1
	if game == 'Garendall': # Pillars of Garendall bug, just use 0xff
		hash2 = core.set_hash2_time(hash2,BitArray('0xff'))
	else:
		hash2 = core.set_hash2_time(hash2,core.get_current_timestamp())
	hash2 = core.make_hash2_valid(hash2)
	return bincode_to_textcode(hash2 ^ hash1)


def generate_code(name,number,game):
	if game != 'EV Nova':
		print('Warning: generated codes will likely fail except for "EV Nova"')
	hash1 = core.get_hash1(name,number,game)
	hash2 = core.get_hash2(name,number,game)
	return bincode_to_textcode(hash1 ^ hash2)


if __name__ == '__main__':
	try:
		if argv[1] == 'date' and (len(argv) == 7 or len(argv) == 6):
			if len(argv) == 7:
				print(date_code(argv[2],argv[3],int(argv[4]),argv[5],int(argv[6])))
			else:
				print(date_code(argv[2],argv[3],int(argv[4]),argv[5]))
		elif argv[1] == 'renew' and len(argv) == 6:
			print(renew_code(argv[2],argv[3],int(argv[4]),argv[5]))
		elif argv[1] == 'generate' and len(argv) == 5:
			print(generate_code(argv[2],int(argv[3]),argv[4]))
		else:
			raise
	except:
		usage = """Usage\n-----\n
Renew codes with "renew" command:
renew <code> "<name>" <number> "<game>"\n
Check approximate date of a code with "date" command:
date <code> "<name>" <number> "<game>" (optional: decade_offset)\n
Generate codes with "generate" command
generate "<name>" <number> "<game>"\n"""
		print(usage)
