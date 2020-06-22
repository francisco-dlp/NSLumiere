import serial
import time
import numpy
import random
		

ser = serial.Serial()
ser.baudrate=9600
ser.port='COM4'
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.bytesize=serial.EIGHTBITS

ser.timeout=2
print(ser)
ser.open()
print(ser.is_open)



ser.write(b'SY 0,0\r')
print(ser.read(6))



ser.close()

print(ser.is_open)