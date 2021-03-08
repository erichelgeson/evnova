from bitstring import BitArray, BitStream
from collections import deque
from datetime import datetime, timedelta



### SUPPORT FUNCTIONS
# binary conversion support
def bits_to_int(b): # 2's comp conversion from bit
  if b.bin[0] == '1':
    b.invert()
    return (int(b.bin,2) + 1) * -1
  else:
    return int(b.bin,2)

def int_to_bits(i): # 2's comp conversion to bit
  if i < 0:
    b = BitArray('0b' + format((i * -1) - 1,'032b'))
    b.invert()
    return b
  else:
    return BitArray('0b' + format(i,'032b'))

def char_to_bits(c):
  return BitArray('0b' + format(ord(c),'032b'))

# 2's complement addition
def addi(a,b):
  return int_to_bits(bits_to_int(a) + b)

# rotation and masking operations
def rotate(bits,num):
  b = deque(bits)
  b.rotate(num)
  return BitArray(b)

def rotate_mask_and(rb,num_shift,num_mask_start,num_mask_end):
  mask = BitArray(32)
  mask[num_mask_start:num_mask_end+1] = [True]*(num_mask_end+1-num_mask_start)
  return rotate(rb,num_shift) & mask

def rotate_mask_insert(ra,rb,num_shift,num_mask_start,num_mask_end):
  mask = BitArray(32)
  mask[num_mask_start:num_mask_end+1] = [True]*(num_mask_end+1-num_mask_start)
  return (ra & ~mask) | (rotate(rb,num_shift) & mask)



### HASH1
def get_hash1(name,number,game):
  key_lower = BitArray(32) # 4-byte key to process on
  key_upper = BitArray(32) # holds overflow values

  name = name.upper().replace(' ','')

  (key_lower,key_upper) = get_hash1_game(game,number,key_lower,key_upper)
  (key_lower,key_upper) = get_hash1_name(name,number,key_lower,key_upper)

  key_upper[0:4] = BitArray(4) # zero out top nibble

  return key_upper + key_lower

def get_hash1_game(string,number,code,overflow):
  r5 = number
  r0 = code
  r9 = overflow
  for i in range(0,len(string)):

    r8 = BitArray('0b' + format(ord(string[i]),'032b'))

    r6 = i + 7
    r7 = r0 << 4
    r10 = r7
    r10[28:32] ^= r9[0:4]
    r9 <<= 4
    r9[28:32] ^= r0[0:4]
    r7 = BitArray('0b' + format(r5 * r6,'032b'))
    r0 = r8 >> 31
    r10 ^= r8
    r6 = r9 ^ r0
    r0 = r10 << 1
    r8 = r6 << 1
    r0[31:32] ^= r6[0:1]
    r8[31:32] ^= r10[0:1]
    r0 ^= r7
    r9 = r8

  code = r0
  overflow = r9
  return (code,overflow)

def get_hash1_name(string,number,code,overflow):
  r5 = number
  r0 = code
  r9 = overflow
  for i in range(0,len(string)):

    r6 = BitArray('0b' + format(ord(string[i]),'032b'))

    r3 = i + 13
    r3 *= r5
    r10 = r0 << 3
    r7 = r9 << 3
    r10[29:32] ^= r9[0:3]
    r7[29:32] ^= r0[0:3]
    r0 = r6 >> 31
    r10 ^= r6
    r8 = r7 ^ r0
    r6 = BitArray('0b' + format(r3 * 3,'032b'))
    r0 = r10 << 1
    r7 = r8 << 1
    r0[31:32] ^= r8[0:1]
    r7[31:32] ^= r10[0:1]
    r0 ^= r6
    r9 = r7
      
  code = r0
  overflow = r9 
  return (code,overflow)



### HASH2
def get_hash2(name,number,game):
  hash2 = BitArray(64)

  f1 = make_hash2_f1(name,number,game)
  f2 = make_hash2_f2(name,number,game)

  hash2 = set_hash2_f1(hash2,f1)
  hash2 = set_hash2_f2(hash2,f2)
  hash2 = clear_hash2_unused(hash2)
  hash2 = set_hash2_time(hash2,get_current_timestamp())
  hash2 = make_hash2_valid(hash2)

  return hash2


def make_hash2_valid(hash2):
  (is_valid, expected, actual) = check_hash2_valid(hash2)
  if not is_valid:
    hash2[61:] = expected
  return hash2

def check_hash2_valid(hash2):
  region = hash2[5:61]
  region = BitArray('0b0') + region # pad front with 0 for divisible by 3

  total = 0
  for i in range(0,19): # order doesn't matter since just adding
    total += int(region[i*3:i*3+3].bin,2)

  expected = BitArray('0b' + format(total,'032b'))[29:]
  actual = hash2[61:]

  return (expected == actual, expected, actual)


def get_current_timestamp():
  return datetime_to_timestamp(datetime.utcnow())

def datetime_to_timestamp(date):
  # need number of fortnights passed since 2000/12/25 (Eastern Time)
  basedate = datetime(2000, 12, 25, 4, 0) # UTC time is 4 hrs ahead Eastern

  weeks = (date - basedate).days / 7
  fortnights = int(weeks / 2)
  return BitArray('0b' + format(fortnights % 256,'08b'))

def timestamp_to_datetime(stamp,decade=0):
  # timestamps hold 256 fortnights, about 512 weeks or 10 years
  # by default, assume first decade but can manually advance if needed
  basedate = datetime(2000, 12, 25, 4, 0) # Christmas Day 2000 in New York, UTC time

  fortnights = int(stamp.bin,2) + (256 * decade)
  weeks = fortnights * 2
  days = weeks * 7
  date = basedate + timedelta(days=days)

  return "~ " + date.strftime("%B %d, %Y")

def set_hash2_time(hash2,timestamp):
  hash2[9] = timestamp[7]
  hash2[14] = timestamp[6]
  hash2[23] = timestamp[5]
  hash2[28] = timestamp[4]
  hash2[37] = timestamp[3]
  hash2[42] = timestamp[2]
  hash2[51] = timestamp[1]
  hash2[56] = timestamp[0]
  return hash2

def get_hash2_time(hash2):
  timestamp = BitArray(8)
  timestamp[7] = hash2[9]
  timestamp[6] = hash2[14]
  timestamp[5] = hash2[23]
  timestamp[4] = hash2[28]
  timestamp[3] = hash2[37]
  timestamp[2] = hash2[42]
  timestamp[1] = hash2[51]
  timestamp[0] = hash2[56]
  return timestamp


def clear_hash2_unused(hash2):
  empty = BitArray(64)
  hash2[0:5] = empty[0:5] # top 5 bits can all be 0
  hash2[24:28] = empty[24:28]
  hash2[10:14] = empty[11:15]
  hash2[52:56] = empty[52:56]
  hash2[38:42] = empty[38:42]
  return hash2

# can be any multiple of the base factors, the functions included just return 1x
def set_hash2_f1(hash2,f1):
  hash2[5:9] = f1[0:4]
  hash2[47:51] = f1[4:8]
  hash2[33:37] = f1[8:12]
  hash2[19:23] = f1[12:16]
  return hash2

def set_hash2_f2(hash2,f2):
  hash2[43:47] = f2[0:4]
  hash2[29:33] = f2[4:8]
  hash2[15:19] = f2[8:12]
  hash2[57:61] = f2[12:16]
  return hash2

def get_hash2_f1(hash2):
  return hash2[5:9] + hash2[47:51] + hash2[33:37] + hash2[19:23]

def get_hash2_f2(hash2):
  return hash2[43:47] + hash2[29:33] + hash2[15:19] + hash2[57:61]

# neither f3 nor topbit have separate validation, can just be 0
def get_hash2_f3(hash2):
  return hash2[24:28] + hash2[10:14] + hash2[52:56] + hash2[38:42]

def get_hash2_topbit(hash2):
  return hash2[4]


# main functions for the basekey factors
# these functions for EV Nova only
def make_hash2_f1(name,number,game):
  name = name.upper().replace(' ','')
  ln = len(name)

  r31 = int_to_bits(number)

  r3 = BitArray(32)
  r3 = addi(r3,-100)
  r0 = char_to_bits(name[12%ln])
  r25 = char_to_bits(game[0]) # E
  r3 = r3 ^ r0
  r0 = char_to_bits(name[15%ln])
  r3 = addi(r3,-61)
  r4 = rotate_mask_and(r3,0,24,31)
  r3 = r4 >> 6
  r3 = r3 ^ rotate_mask_and(r4,-2,22,29)
  r4 = rotate_mask_and(r3,0,24,31)
  r4 = r4 ^ r25
  r4 = r4 ^ r0
  r3 = rotate_mask_and(r4,-29,27,31)
  r3 = r3 ^ rotate_mask_and(r4,-5,19,26)
  r0 = rotate_mask_and(r3,-26,30,31)
  r0 = r0 ^ rotate_mask_and(r3,-2,22,29)
  r3 = rotate_mask_and(r0,0,24,31)
  r3 = addi(r3,82)
  r0 = rotate_mask_and(r3,-7,17,24)
  r0 = rotate_mask_insert(r0,r3,-31,25,31)
  r7 = rotate_mask_and(r0,0,24,31)
  r7 = addi(r7,99)
  r0 = rotate_mask_and(r7,0,24,31)

  if int(r0.bin,2) > int("71",16):
    r0 = rotate_mask_and(r31,0,24,31)
    r0 = r7 ^ r0
    r7 = rotate_mask_and(r0,0,24,31)

  r3 = char_to_bits(name[3%ln])
  r0 = rotate_mask_and(r31,0,24,31)
  r5 = char_to_bits(name[6%ln])
  r7 = r7 ^ r3
  r4 = char_to_bits(name[5%ln])
  r6 = rotate_mask_and(r7,-1,23,30)
  r3 = char_to_bits(game[3]) # N
  r6 = rotate_mask_insert(r6,r7,-25,31,31)
  r28 = char_to_bits(game[0]) # E
  r6 = rotate_mask_and(r6,0,24,31)
  r6 = r6 ^ r5
  r6 = r6 ^ r4
  r4 = rotate_mask_and(r6,0,24,31)
  r18 = addi(r4,-42)
  r18 = r18 ^ r3
  r18 = r18 ^ r0
  r18 = addi(r18,-87)
  r18 = r18 ^ r28

  # proc235 returns value in r3, unused    

  r3 = addi(r18,89)
  r0 = rotate_mask_and(r3,0,24,31)
  r0 = r0 >> 7
  r0 = r0 ^ rotate_mask_and(r3,-1,23,30)
  r3 = rotate_mask_and(r0,0,24,31)
  r3 = addi(r3,int("-73",16))
  r0 = rotate_mask_and(r3,-29,27,31)
  r0 = r0 ^ rotate_mask_and(r3,-5,19,26)
  r3 = rotate_mask_and(r0,-27,29,31)
  r3 = r3 ^ rotate_mask_and(r0,-3,21,28)
  r0 = rotate_mask_and(r3,-5,19,26)
  r0 = rotate_mask_insert(r0,r3,-29,27,31)
  r18 = rotate_mask_and(r0,0,24,31)
  r0 = rotate_mask_and(r31,0,24,31)
  r18 = r18 ^ r0
  r18 = addi(r18,int("AC",16))
  r0 = rotate_mask_and(r18,0,24,31)

  if int(r0.bin,2) > int("90",16):
    r0 = char_to_bits(name[4%ln])
    r0 = r18 ^ r0
    r18 = rotate_mask_and(r0,0,24,31)

  # proc235 returns value in r3, unused    

  r7 = addi(r18,-64)
  r4 = char_to_bits(game[6]) # a
  r6 = rotate_mask_and(r7,-26,30,31)
  r5 = char_to_bits(name[9%ln])
  r6 = r6 ^ rotate_mask_and(r7,-2,22,29)
  r3 = char_to_bits(name[2%ln])
  r6 = rotate_mask_and(r6,0,24,31)
  r0 = char_to_bits(name[12%ln])
  r6 = r6 ^ r4
  r6 = r6 ^ r5
  r6 = r6 ^ r3
  r6 = r6 ^ r28
  r4 = addi(r6,-39)
  r3 = rotate_mask_and(r4,-31,25,31)
  r3 = r3 ^ rotate_mask_and(r4,-7,17,24)
  r3 = rotate_mask_and(r3,0,24,31)
  r3 = r3 ^ r5
  r3 = r3 ^ r0
  r0 = rotate_mask_and(r31,0,24,31)
  r3 = r3 ^ r0
  r0 = rotate_mask_and(r3,-7,17,24)
  r0 = rotate_mask_insert(r0,r3,-31,25,31)
  r18 = rotate_mask_and(r0,0,24,31)
  r3 = r18

  # proc20 returns value in r3, unused

  r0 = rotate_mask_and(r31,0,24,31)
  r18 = r18 ^ r0
  r0 = addi(r18,int("-69",16))
  r3 = rotate_mask_and(r0,-25,31,31)
  r3 = r3 ^ rotate_mask_and(r0,-1,23,30)
  r0 = rotate_mask_and(r3,-7,17,24)
  r0 = rotate_mask_insert(r0,r3,-31,25,31)
  r19 = rotate_mask_and(r0,0,24,31)

  # proc235 returns value in r3, unused    

  r3 = r19

  # proc20 returns value in r3, unused

  r26 = char_to_bits(game[5]) # v
  r19 = addi(r19,int("66",16))
  r19 = r19 ^ r26
  r19 = addi(r19,int("-81",16))
  r0 = rotate_mask_and(r19,0,24,31)

  if int(r0.bin,2) > 10:
    r0 = addi(r19,-8)
    r19 = rotate_mask_and(r0,0,24,31)

  r0 = rotate_mask_and(r19,0,24,31)
  r7 = char_to_bits(game[3]) # N
  r3 = r0 >> 4
  r5 = char_to_bits(name[14%ln])
  r3 = r3 ^ rotate_mask_and(r19,-4,20,27)
  r6 = char_to_bits(game[4]) # o
  r9 = rotate_mask_and(r3,0,24,31)
  r0 = char_to_bits(name[12%ln])
  r8 = r9 >> 1
  r4 = char_to_bits(game[1]) # V
  r8 = r8 ^ rotate_mask_and(r9,-7,17,24)
  r3 = char_to_bits(name[4%ln])
  r9 = rotate_mask_and(r8,0,24,31)
  r8 = r9 >> 5
  r8 = r8 ^ rotate_mask_and(r9,-3,21,28)
  r8 = rotate_mask_and(r8,0,24,31)
  r8 = r8 ^ r7
  r8 = rotate_mask_and(r8,0,24,31)
  r7 = r8 >> 4
  r7 = r7 ^ rotate_mask_and(r8,-4,20,27)
  r8 = rotate_mask_and(r7,0,24,31)
  r7 = r8 >> 7
  r7 = r7 ^ rotate_mask_and(r8,-1,23,30)
  r8 = rotate_mask_and(r7,0,24,31)
  r8 = r8 ^ r26
  r7 = rotate_mask_and(r8,0,24,31)
  r7 = r7 >> 4
  r7 = r7 ^ rotate_mask_and(r8,-4,20,27)
  r7 = rotate_mask_and(r7,0,24,31)
  r7 = addi(r7,62)
  r7 = r7 ^ r5
  r7 = r7 ^ r28
  r5 = rotate_mask_and(r31,0,24,31)
  r7 = r7 ^ r5
  r7 = r7 ^ r6
  r6 = rotate_mask_and(r7,0,24,31)
  r6 = r6 >> 7
  r6 = r6 ^ rotate_mask_and(r7,-1,23,30)
  r7 = rotate_mask_and(r6,0,24,31)
  r7 = addi(r7,-6)
  r7 = r7 ^ r25
  r6 = rotate_mask_and(r7,0,24,31)
  r6 = r6 >> 4
  r6 = r6 ^ rotate_mask_and(r7,-4,20,27)
  r7 = rotate_mask_and(r6,0,24,31)
  r6 = r7 >> 5
  r6 = r6 ^ rotate_mask_and(r7,-3,21,28)
  r7 = rotate_mask_and(r6,0,24,31)
  r6 = r7 >> 3
  r6 = r6 ^ rotate_mask_and(r7,-5,19,26)
  r7 = rotate_mask_and(r6,-31,25,31)
  r7 = r7 ^ rotate_mask_and(r6,-7,17,24)
  r6 = rotate_mask_and(r7,-26,30,31)
  r6 = r6 ^ rotate_mask_and(r7,-2,22,29)
  r7 = rotate_mask_and(r6,0,24,31)
  r7 = addi(r7,-80)
  r7 = r7 ^ r0
  r6 = rotate_mask_and(r7,-2,22,29)
  r6 = rotate_mask_insert(r6,r7,-26,30,31)
  r6 = rotate_mask_and(r6,0,24,31)
  r6 = addi(r6,int("BC",16))
  r6 = r6 ^ r4
  r6 = addi(r6,int("-75",16))
  r6 = r6 ^ r3
  r6 = r6 ^ r0
  r0 = char_to_bits(name[1%ln])
  r3 = rotate_mask_and(r6,-8,16,23)
  r3 = r3 ^ rotate_mask_and(r6,-0,24,31)
  r3 = rotate_mask_and(r3,0,24,31)
  r3 = r3 ^ r0
  r3 = r3 ^ r5
  r0 = rotate_mask_and(r3,0,24,31)
  r0 = r0 >> 1
  r0 = r0 ^ rotate_mask_and(r3,-7,17,24)
  r3 = rotate_mask_and(r0,0,24,31)
  r0 = rotate_mask_and(r0,-27,29,31)
  r0 = r0 ^ rotate_mask_and(r3,-3,21,28)
  r3 = rotate_mask_and(r0,0,24,31)
  r3 = addi(r3,int("69",16))
  r0 = rotate_mask_and(r3,-30,26,31)
  r0 = r0 ^ rotate_mask_and(r3,-6,18,25)
  r3 = rotate_mask_and(r0,-8,16,23)
  r3 = r3 ^ rotate_mask_and(r0,-0,24,31)
  r0 = rotate_mask_and(r3,-3,21,28)
  r0 = rotate_mask_insert(r0,r3,-27,29,31)
  r25 = rotate_mask_and(r0,0,24,31)

  # proc1182 returns current timnestamp in r3    
  # r0 = rotate_mask_and(r3,0,24,31)
  # r19 = rotate_mask_and(r25,-0,29,30)
  # r3 = r25 ^ r0
  # overwritten shortly, so unused
    
  r0 = rotate_mask_and(r19,0,24,31)
  r19 = addi(r19,-1)
  # proc189 call is bypassed as long as r19 minus 1 is not equal to r19[24:]

  r3 = char_to_bits(game[1]) # V
  r0 = char_to_bits(name[12%ln])
  r25 = r25 ^ r3
  r3 = char_to_bits(game[2]) # " "
  r25 = r25 ^ r0
  r0 = char_to_bits(name[1%ln])
  r4 = rotate_mask_and(r25,-6,18,25)
  r4 = rotate_mask_insert(r4,r25,-30,26,31)
  r5 = rotate_mask_and(r4,0,24,31)
  r5 = r5 ^ r3
  r5 = r5 ^ r0
  r0 = rotate_mask_and(r5,0,24,31)

  if int(r0.bin,2) > int("DB",16):
    r0 = r5 ^ r28
    r5 = rotate_mask_and(r0,0,24,31)

  r0 = char_to_bits(name[6%ln])
  r5 = r5 ^ r0
  r0 = rotate_mask_and(r5,0,24,31)

  if int(r0.bin,2) > int("A2",16):
    r5 = r0

  r4 = char_to_bits(name[13%ln])
  r5 = addi(r5,int("7B",16))
  r3 = rotate_mask_and(r31,0,24,31)
  r0 = char_to_bits(name[5%ln])
  r5 = r5 ^ r4
  r5 = r5 ^ r3
  r4 = rotate_mask_and(r5,-25,31,31)
  r4 = r4 ^ rotate_mask_and(r5,-1,23,30)
  r3 = rotate_mask_and(r4,-2,22,29)
  r3 = rotate_mask_insert(r3,r4,-26,30,31)
  r5 = rotate_mask_and(r3,0,24,31)
  r5 = r5 ^ r0
  r0 = rotate_mask_and(r5,0,24,31)

  return r0[16:]


def make_hash2_f2(name,number,game):
  name = name.upper().replace(' ','')
  ln = len(name)

  r31 = BitArray('0b'+format(number,'032b'))

  r19 = BitArray(32)

  r3 = rotate_mask_and(r31,0,24,31)
  r0 = char_to_bits(name[5%ln])
  r19 = r19 ^ r3
  r19 = addi(r19,50)
  r19 = r19 ^ r3
  r3 = rotate_mask_and(r19,0,24,31)

  if int(r3.bin,2) < int(r0.bin,2):
    r0 = addi(r19,90)
    r19 = rotate_mask_and(r0,0,24,31)

  r4 = char_to_bits(game[5]) # v
  r3 = rotate_mask_and(r31,0,24,31)
  r0 = char_to_bits(name[3%ln])
  r19 = r19 ^ r4
  r19 = addi(r19,int("6A",16))
  r19 = r19 ^ r3
  r19 = r19 ^ r0

  # proc235 returns value in r3, unused  

  r0 = char_to_bits(name[14%ln])
  r28 = char_to_bits(game[2]) # " "
  r19 = r19 ^ r0
  r0 = rotate_mask_and(r19,-28,28,31)
  r0 = r0 ^ rotate_mask_and(r19,-4,20,27)
  r3 = rotate_mask_and(r0,0,24,31)
  r3 = r3 ^ r28
  r0 = addi(r3,-28)
  r3 = rotate_mask_and(r0,-8,16,23)
  r3 = r3 ^ rotate_mask_and(r0,-0,24,31)
  r0 = rotate_mask_and(r3,-3,21,28)
  r0 = rotate_mask_insert(r0,r3,-27,29,31)
  r3 = rotate_mask_and(r0,0,24,31)
  r3 = addi(r3,2)
  r0 = rotate_mask_and(r3,0,24,31)

  if int(r0.bin,2) > int("CC",16):
    r0 = rotate_mask_and(r3,-7,17,24)
    r0 = rotate_mask_insert(r0,r3,-31,25,31)
    r3 = rotate_mask_and(r0,0,24,31)

  r0 = rotate_mask_and(r3,-28,28,31)
  r0 = r0 ^ rotate_mask_and(r3,-4,20,27)
  r3 = rotate_mask_and(r0,0,24,31)
  r0 = addi(r3,int("-7C",16))
  r3 = rotate_mask_and(r0,-26,30,31)
  r3 = r3 ^ rotate_mask_and(r0,-2,22,29)
  r0 = rotate_mask_and(r3,-4,20,27)
  r0 = rotate_mask_insert(r0,r3,-28,28,31)
  r18 = rotate_mask_and(r0,0,24,31)

  # proc1162 and proc1161 appear unused, although they change r0-r12 values

  r27 = char_to_bits(game[0]) # E
  r0 = rotate_mask_and(r31,0,24,31)
  r3 = char_to_bits(name[11%ln])
  r18 = r18 ^ r27
  r18 = r18 ^ r3
  r4 = rotate_mask_and(r18,-28,28,31)
  r4 = r4 ^ rotate_mask_and(r18,-4,20,27)
  r3 = rotate_mask_and(r4,-28,28,31)
  r3 = r3 ^ rotate_mask_and(r4,-4,20,27)
  r3 = rotate_mask_and(r3,0,24,31)
  r3 = r3 ^ r0
  r0 = rotate_mask_and(r3,-6,18,25)
  r0 = rotate_mask_insert(r0,r3,-30,26,31)
  r4 = rotate_mask_and(r0,0,24,31)

  if int(r4.bin,2) > int("79",16):
    r0 = char_to_bits(game[0]) # E
    r0 = r4 ^ r0
    r4 = rotate_mask_and(r0,0,24,31)

  r3 = rotate_mask_and(r31,0,24,31)
  r4 = r4 ^ r3
  r0 = rotate_mask_and(r4,-26,30,31)
  r0 = r0 ^ rotate_mask_and(r4,-2,22,29)
  r0 = rotate_mask_and(r0,0,24,31)
  r0 = r0 ^ r3
  r3 = rotate_mask_and(r0,-28,28,31)
  r3 = r3 ^ rotate_mask_and(r0,-4,20,27)
  r0 = rotate_mask_and(r3,-1,23,30)
  r0 = rotate_mask_insert(r0,r3,-25,31,31)
  r18 = rotate_mask_and(r0,0,24,31)

  # bl       proc188
  # mullw    r3,r18,r3
  # seems that r3 is just 1 upon return from 188 in normal operation, so use mr r3,r18
  r3 = r18

  r0 = char_to_bits(game[1]) # V
  r19 = char_to_bits(game[6]) # a
  r3 = rotate_mask_and(r3,0,24,31)
  r18 = r3 ^ r0
  r18 = addi(r18,-47)
  r18 = r18 ^ r19
  r18 = addi(r18,36)
  r0 = rotate_mask_and(r18,0,24,31)
  r26 = r28

  if int(r0.bin,2) < int(r26.bin,2):
    r0 = char_to_bits(name[8%ln])
    r0 = r18 ^ r0
    r18 = rotate_mask_and(r0,0,24,31)

  r3 = rotate_mask_and(r31,0,24,31)
  r0 = char_to_bits(game[4]) # o
  r18 = r18 ^ r3
  r18 = r18 ^ r0

  # proc1162 and proc1161 appear unused, although they change r0-r12 values

  r4 = char_to_bits(name[9%ln])
  r0 = char_to_bits(name[0%ln])
  r18 = r18 ^ r4
  r18 = r18 ^ r0
  r18 = rotate_mask_and(r18,0,24,31)

  # lbzx     r3,r21,r18
  # addi     r0,r3,1   
  # stbx     r0,r21,r18
  # this snippet appears to be storing some sort of counter
  # perhaps used when flagging too many attempts or invalid codes
  # (codes can be blacklisted locally in the saved license file)

  if int(r18.bin,2) > int(r0.bin,2):
    r0 = r18 << 7
    r0 = rotate_mask_insert(r0,r18,-31,25,31)
    r18 = rotate_mask_and(r0,0,24,31)

  r18 = addi(r18,29)
  r18 = r18 ^ r28
  r18 = r18 ^ r4

  # proc235 returns value in r3, unused

  r3 = char_to_bits(name[2%ln]) # C
  r0 = rotate_mask_and(r31,0,24,31)
  r18 = r18 ^ r3
  r3 = rotate_mask_and(r18,-6,18,25)
  r3 = rotate_mask_insert(r3,r18,-30,26,31)
  r21 = rotate_mask_and(r3,0,24,31)
  r21 = r21 ^ r19
  r21 = r21 ^ r0

  # proc235 returns value in r3, unused

  r0 = rotate_mask_and(r31,0,24,31)
  r4 = char_to_bits(name[6%ln])
  r21 = addi(r21,int("-C3",16))
  r28 = char_to_bits(game[2]) # " '"
  r21 = r21 ^ r0
  r3 = char_to_bits(name[3%ln])
  r5 = rotate_mask_and(r21,-8,16,23)
  r5 = r5 ^ rotate_mask_and(r21,-0,24,31)
  r6 = rotate_mask_and(r5,0,24,31)
  r5 = r6 >> 5
  r5 = r5 ^ rotate_mask_and(r6,-3,21,28)
  r5 = rotate_mask_and(r5,0,24,31)
  r6 = addi(r5,-3)
  r5 = rotate_mask_and(r6,-8,16,23)
  r5 = r5 ^ rotate_mask_and(r6,-0,24,31)
  r5 = rotate_mask_and(r5,0,24,31)
  r5 = addi(r5,-60)
  r5 = rotate_mask_and(r5,0,24,31)
  r6 = r5 ^ r27
  r5 = rotate_mask_and(r6,0,24,31)
  r5 = r5 >> 1
  r5 = r5 ^ rotate_mask_and(r6,-7,17,24)
  r6 = rotate_mask_and(r5,0,24,31)
  r5 = r6 >> 3
  r5 = r5 ^ rotate_mask_and(r6,-5,19,26)
  r5 = rotate_mask_and(r5,0,24,31)
  r6 = addi(r5,8)
  r5 = rotate_mask_and(r6,0,24,31)
  r5 = r5 >> 2
  r5 = r5 ^ rotate_mask_and(r6,-6,18,25)
  r5 = rotate_mask_and(r5,0,24,31)
  r5 = r5 ^ r4
  r5 = r5 ^ r28
  r5 = r5 ^ r3
  r5 = addi(r5,-27)
  r5 = r5 ^ r0
  r0 = rotate_mask_and(r5,0,24,31)
  r0 = r0 >> 5
  r0 = r0 ^ rotate_mask_and(r5,-3,21,28)
  r3 = rotate_mask_and(r0,-31,25,31)
  r3 = r3 ^ rotate_mask_and(r0,-7,17,24)
  r0 = rotate_mask_and(r3,-30,26,31)
  r0 = r0 ^ rotate_mask_and(r3,-6,18,25)
  r3 = rotate_mask_and(r0,0,24,31)
  r3 = addi(r3,-71)
  r0 = rotate_mask_and(r3,-2,22,29)
  r0 = rotate_mask_insert(r0,r3,-26,30,31)
  r4 = rotate_mask_and(r0,0,24,31)
  r0 = r28

  if int(r4.bin,2) > int(r0.bin,2):
    r0 = r4 << 2
    r0 = rotate_mask_insert(r0,r4,-26,30,31)
    r4 = rotate_mask_and(r0,0,24,31)

  r3 = char_to_bits(name[13%ln]) # S
  r4 = addi(r4,75)
  r0 = char_to_bits(name[8%ln]) # L
  r4 = r4 ^ r3
  r4 = r4 ^ r0
  r0 = rotate_mask_and(r4,0,24,31)

  if int(r0.bin,2) < 44:
    r0 = addi(r4,-53)
    r4 = rotate_mask_and(r0,0,24,31)

  r3 = addi(r4,73)
  r0 = rotate_mask_and(r3,-6,18,25)
  r0 = rotate_mask_insert(r0,r3,-30,26,31)
  r18 = rotate_mask_and(r0,0,24,31)

  # these next few lines seem irrelevant if skipping proc235
  # cmp      cr0,0,r18,r26       
  # bc       IF_NOT,cr0_GT,lak_41
  # bl       proc235             

  r0 = char_to_bits(name[10%ln])
  r4 = rotate_mask_and(r31,0,24,31)
  r6 = char_to_bits(name[14%ln])
  r18 = r18 ^ r0
  r5 = char_to_bits(name[6%ln])
  r8 = addi(r18,-45)
  r3 = char_to_bits(name[4%ln])
  r7 = rotate_mask_and(r8,0,24,31)
  r0 = char_to_bits(name[3%ln])
  r7 = r7 >> 1
  r7 = r7 ^ rotate_mask_and(r8,-7,17,24)
  r7 = rotate_mask_and(r7,0,24,31)
  r7 = addi(r7,34)
  r7 = r7 ^ r6
  r6 = rotate_mask_and(r7,0,24,31)
  r6 = r6 >> 6
  r6 = r6 ^ rotate_mask_and(r7,-2,22,29)
  r6 = rotate_mask_and(r6,0,24,31)
  r6 = r6 ^ r5
  r5 = rotate_mask_and(r6,0,24,31)
  r5 = r5 >> 5
  r5 = r5 ^ rotate_mask_and(r6,-3,21,28)
  r6 = rotate_mask_and(r5,0,24,31)
  r5 = rotate_mask_and(r5,-29,27,31)
  r5 = r5 ^ rotate_mask_and(r6,-5,19,26)
  r5 = rotate_mask_and(r5,0,24,31)
  r5 = r5 ^ r3
  r5 = r5 ^ r4
  r5 = r5 ^ r4
  r5 = r5 ^ r4
  r5 = addi(r5,86)
  r5 = r5 ^ r28
  r3 = rotate_mask_and(r5,-25,31,31)
  r3 = r3 ^ rotate_mask_and(r5,-1,23,30)
  r5 = rotate_mask_and(r3,0,24,31)
  r5 = r5 ^ r4
  r3 = rotate_mask_and(r5,-7,17,24)
  r3 = rotate_mask_insert(r3,r5,-31,25,31)
  r19 = rotate_mask_and(r3,0,24,31)
  r19 = r19 ^ r0
  r19 = r19 ^ r4

  # proc235 returns value in r3, unused

  r19 = addi(r19,int("6D",16))
  r0 = rotate_mask_and(r19,0,24,31)

  return r0[16:]
