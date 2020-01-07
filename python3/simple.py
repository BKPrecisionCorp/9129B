import serial

ser = serial.Serial("/dev/ttyUSB1")
ser.timeout = 1

ser.write("syst:rem\n".encode())
ser.write("*idn?\n".encode())
print(ser.read(40))

#setup channel 2
ser.write("inst ch2\n".encode())
ser.write("volt 1.23\n".encode())
ser.write("chan:outp on\n".encode())
