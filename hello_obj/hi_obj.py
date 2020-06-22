import serial
import time
import numpy
import random
		

ser = serial.Serial()
ser.baudrate=57600
ser.port='COM13'
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.bytesize=serial.EIGHTBITS

ser.timeout=2
print(ser)
ser.open()
print(ser.is_open)



ser.write(b'>1,2,1\r')
print(ser.readline())

ser.write(b'>1,1,1,0.5,0.5\r')
print(ser.readline())


ser.close()

print(ser.is_open)