import serial
import time

# BK Precision Example Code is hosted here:
# https://github.com/BKPrecisionCorp/9129B/blob/master/python3/simple.py
# It's not much.
#
# Programming Manual is available here:
# https://bkpmedia.s3.amazonaws.com/downloads/programming_manuals/en-us/9129B_programming_manual.pdf
#
# Note:
#
# TODO: Calibration commands...
# LOL NO. If you know what they are for, this implementation should be
# sufficient to implement them yourself. I have no desire for that functionality.

class BK_9129B:
	# Output Mode
	_mode = 0 # Device has 3 output modes and handles each as follows
		# 0 : All Channels are treated as independent
		# 1 : Channels 1+2 are treated in series (shared limits)
		#     The output voltage is specified as the sum of the channels
		# 2 : Channels 1+2 are treated in parallel (shared limits)
		#	  The output current is specified as the sum of the channels
	# Serial Port
	_serial = None # Serial Object
	# Serial Configuration
	_BAUD_RATE = [4800, 9600, 38400] # 9600 Baud is default
	_DEFAULT_ADDRESS = 0
	_PARITY = None
	_STOP_BIT = 1
	# Command table
	_COMMANDS = {
		'ClearProtect'  : 'OUTP:PROT:CLE', # Clear protected power supply
		'EndByte'       : '\n', # End byte
		'GetCCOutputI'  : 'SOUR:CURR?',    # Get the output current set point (current channel)
		'GetCCOutputV'  : 'SOUR:VOLT?',    # Get the output current set point (current channel)
						   # WARNING: This behaviour depends on an UNDOCUMENTED instruction
		'GetChannel'    : 'INST:NSEL?',    # Queries the active channel
		'GetCurrent'    : 'MEAS:CURR',     # Get the present, MEASURED output current
		'GetOutputEn3'  : 'SOUR:APP:OUT?', # Get output state of all 3 channels
		'GetOutputI'    : 'SOUR:APP:CURR?',# Get the output current set point
		'GetOutputV'    : 'SOUR:APP:VOLT?',# Get the output voltage set point
						   # WARNING: This behaviour depends on an UNDOCUMENTED instruction
		'GetVoltage'    : 'MEAS:VOLT',     # Get the present, MEASURED output voltage
		'GetOutputEn'   : 'OUTP:STAT?',    # Query if Output is configured as (independent)
		'IsMode1'       : 'OUTP:SER?',     # Query if Output is configured as (series)
		'IsMode2'       : 'OUTP:PARA?',    # Query if Output is configured as (parallel)
		'OutputEnable'  : 'OUTP:STAT',     # Setting the output on/off state
		'OutputMode1'   : 'OUTP:SER',      # Configure the output in series
		'OutputMode2'   : 'OUTP:PARA',     # Configure the output in parallel
		'RemoteDisable' : 'SYST:LOC',      # Enable local control mode (disable remote control)
		'RemoteEnable'  : 'SYST:REM',      # Enable remote control mode
		'SelectChannel' : 'INST:NSEL',     # Selects active channel of instrument
		'SetOutputI'    : 'SOUR:CURR',     # Setting the output current (of a specific channel)
		'SetOutputV'    : 'SOUR:VOLT',     # Setting the output voltage (of a sepcific channel)
						   # WARNING: This behaviour depends on an UNDOCUMENTED instruction
		'StartByte'     : '', # Start byte
	}
	def __init__(self, com):
		self._serial = com
		# Set the output mode
		mode = self._get_mode()
		self._mode = mode
	def _get_mode(self):
		# Test for Series Operation
		self._sendln(self._COMMANDS['IsMode1'])
		ret = int(self._serial.readline()[:-1])
		if(ret == 1): return 1
		# Test for Parallel Operation
		self._sendln(self._COMMANDS['IsMode2'])
		ret = int(self._serial.readline()[:-1])
		if(ret == 1): return 2
		# Otherwise Assume Independent Operation
		else: return 0
	def _sel_ch(self, ch, retry_lim = 10):
		# Attempts to select specified channel for control
		# Retries if channel is not selected, returns False if unsuccessful
		ii = 0
		success = False
		cmd = f"{self._COMMANDS['SelectChannel']} {int(ch)}"
		while( (success == False) and (ii < retry_lim) ):
			# Send the Command
			self._sendln(cmd)
			# Send the Query
			self._sendln(self._COMMANDS['GetChannel'])
			# Ensure query is consistent with desired outcome
			resp = self._serial.readline()[:-1]
			if (int(resp) == int(ch)):
				success = True
			ii = ii + 1
		return success
	def _sendln(self, str):
		out_cmd = (str + self._COMMANDS['EndByte']).encode()
		self._serial.write(out_cmd)
	def close(self):
		self.output_disable()
		self.remote_control(enable = False)
	def get_output_status(self):
		self._sendln(self._COMMANDS['GetOutputEn3'])
		ret = self._serial.readline()
		return [bool(int(a)) for a in ret[:-1].decode("utf-8").split(", ")]
	def get_output_current(self):
		# Returns Measured Output Current
		self._sendln(self._COMMANDS['GetCurrent'] + ":ALL?")
		ret = self._serial.readline()
		return [float(a) for a in ret[:-1].decode("utf-8").split(", ")]
	def get_output_current_sp(self):
		# Returns Output Current Limit (Desired / Set Point)
		self._sendln(self._COMMANDS['GetOutputI'])
		ret = self._serial.readline()
		print('current_sp:' + ret.decode("utf-8"))
		return [float(a) for a in ret[:-1].decode("utf-8").split(", ")]
	def get_output_voltage(self):
		# Returns Output Current Limit (Desired / Set Point)
		self._sendln(self._COMMANDS['GetVoltage'] + ":ALL?")
		ret = self._serial.readline()
		return [float(a) for a in ret[:-1].decode("utf-8").split(", ")]
	def get_output_voltage_sp(self):
		# Returns Output Current Limit (Desired / Set Point)
		self._sendln(self._COMMANDS['GetOutputV'])
		ret = self._serial.readline()
		print('voltage_sp:' + ret.decode("utf-8"))
		return [float(a) for a in ret[:-1].decode("utf-8").split(", ")]
	def get_status(self):
		status = {}
		status['output_enable'] = self.get_output_status()
		status['output_current'] = self.get_output_current()
		status['output_voltage'] = self.get_output_voltage()
		status['target_current'] = self.get_output_current_sp()
		status['target_voltage'] = self.get_output_voltage_sp()
		return status
	def output_enable(self, enable = True):
		# Enables the Output (enable = True, default)
		# for (enable = False) output is disabled
		cmd = self._COMMANDS['OutputEnable']
		cmd += ' 1' if(enable == True) else ' 0' # The space is INTENTIONAL
		self._sendln(cmd)
	def output_disable(self): self.output_enable(False)
	def remote_control(self, enable = True):
		# Enables Remote Control of Device
		# Native command does not have a return type
		# TODO: STATUS CHECKING TO VERIFY
		if(enable == True):
			cmd = self._COMMANDS['RemoteEnable']
		else:
			cmd = self._COMMANDS['RemoteDisable']
		self._sendln(cmd)
	def set_output_current(self, current, ch = 1):
		success = False
		# Format the setpoint
		if (current < 1.00):
			cur_str = f"{(current*1000.0):.3f}mA"
		else:
			cur_str = f"{current:0.3f}A"
		cmd = f"{self._COMMANDS['SetOutputI']} {cur_str}"
		if(self._sel_ch(ch)): # Set Supply to Desired Channel
			ii = 0
			while( (success == False) and (ii < 10) ):
				self._sendln(cmd)
				# Verify Result
				self._sendln(self._COMMANDS['GetCCOutputI'])
				ret = self._serial.readline()[:-1]
				if( abs(float(ret) - current) < 0.0005 ): success = True
				ii = ii + 1
		return success
	def set_output_mode(self, mode):
		if(mode == 1): # Series Mode
			self._sendln(self._COMMANDS['OutputMode1'] + ' 1')
			self._mode = 1
		elif(mode == 2): # Parallel Mode
			self._sendln(self._COMMANDS['OutputMode2'] + ' 1')
			self._mode = 2
		else: # Independent Mode
			self._sendln(self._COMMANDS['OutputMode1'] + ' 0')
			self._sendln(self._COMMANDS['OutputMode2'] + ' 0')
			self._mode = 0
	def set_output_voltage(self, voltage, ch = 1):
		# Assumes Voltage Per Channel;
		# In series case the total output voltage is the specified amount
		# Which correlates is a per-channel voltage of 1/2 nominal
		success = False
		cmd = f"{self._COMMANDS['SetOutputV']} {voltage:.2f}"
		if(self._sel_ch(ch)): # Set Supply to Desired Channel
			ii = 0
			while( (success == False) and (ii < 10) ):
				self._sendln(cmd)
				# Verify Result
				self._sendln(self._COMMANDS['GetCCOutputV'])
				ret = self._serial.readline()[:-1]
				if( abs(float(ret) - voltage) < 0.005 ): success = True
				ii = ii + 1
		return success
	
if __name__ == "__main__":
	ser = serial.Serial('COM11', timeout=1)  # open serial port
	PSU = BK_9129B(ser)

	PSU.remote_control()
	PSU.set_output_mode(1)
	PSU.set_output_current(0.150, 1)
	PSU.set_output_voltage(12, 1)
	PSU.set_output_current(0.250, 3)
	PSU.set_output_voltage(5, 3)
	PSU.output_enable()
	time.sleep(1)
	print(PSU.get_status())	
	PSU.close()