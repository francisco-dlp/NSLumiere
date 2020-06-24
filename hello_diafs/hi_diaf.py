import serial
import time
import numpy
import random
		

ser = serial.Serial()
ser.baudrate=9600
ser.port='COM7'
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.bytesize=serial.EIGHTBITS

ser.timeout=2
print(ser)
ser.open()
print(ser.is_open)

data=bytearray([1, 20, 251, 93, 1, 0])
print(data)

#ser.write(b'\x01\x14\xfb\x5d\x01\x00')
ser.write(data)
print(ser.read(6))


#ser.write(b'>1,1,1,0.5,0.5\r')
#print(ser.readline())


ser.close()

print(ser.is_open)