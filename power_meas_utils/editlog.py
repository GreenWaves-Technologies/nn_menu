import os
import csv
import sys
import numpy as np
import pickle
import re

if len(sys.argv) != 5:
    print("Wrong number of arguments!")
    exit(1)

file_csv = str(sys.argv[1])
file_at = str(sys.argv[2])
file_log = str(sys.argv[3])
file_name = str(sys.argv[4])

csv.field_size_limit(20000000)

# log file
at_log = {}


# parse power measurements
with open(file_csv, newline='') as f:
	reader = csv.reader(f)
	for r, row in enumerate(reader):
		print(row[0], float(row[1]))
		if len(row) == 2:
			at_log[row[0]] = float(row[1])


# parse at file
L1_MEM_USAGE = re.compile(r'\s*(?P<column>Shared L1 Memory size) \(Bytes\)\s+\: Given\:\s+(?P<given>[0-9]+)\,\sUsed\:\s+(?P<used>[0-9]+)')
L2_MEM_USAGE = re.compile(r'\s*(?P<column>L2 Memory size) \(Bytes\)\s+\: Given\:\s+(?P<given>[0-9]+)\,\sUsed\:\s+(?P<used>[0-9]+)')
L3_MEM_USAGE = re.compile(r'\s*(?P<column>L3 Memory size) \(Bytes\)\s+\: Given\:\s+(?P<given>[0-9]+)\,\sUsed\:\s+(?P<used>[0-9]+)')
L3_MEM_BW = re.compile(r'(?P<column>L3 Memory bandwidth for 1 graph run)\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n')
L2_MEM_BW = re.compile(r'(?P<column>L2 Memory bandwidth for 1 graph run)\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n')
KER_ARGS = re.compile(r'(?P<column>Sum of all Kernels arguments size)\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n')
TIL_OH = re.compile(r'(?P<column>Tiling Bandwith overhead)\s+\:\s+(?P<value>[0-9.]+)\s+Move/KerArgSize\n')
L2_MEM_BW_PER = re.compile(r'(?P<column>Percentage of baseline BW for L2)\s+\:\s+(?P<value>[0-9.]+)\s+\%\n')
L3_MEM_BW_PER = re.compile(r'(?P<column>Percentage of baseline BW for L3)\s+\:\s+(?P<value>[0-9.]+)\s+\%\n')
KER_OPS = re.compile(r'(?P<column>Sum of all Kernels operations)\s+\:\s+(?P<value>[0-9]+)\s+Operations\n')
TOT_COEFFS = re.compile(r'(?P<column>Total amount of flash coefficients)\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n')

matches = [L3_MEM_BW, L2_MEM_BW, TIL_OH, KER_ARGS, L2_MEM_BW_PER, L3_MEM_BW_PER, KER_OPS, TOT_COEFFS,L1_MEM_USAGE, L2_MEM_USAGE, L3_MEM_USAGE]

with open(file_at, newline='') as f:
	out_log = f.readlines()
	row = []
	for line in out_log:
		for match in matches:
			m = match.search(line)
			if m:
				metric = m['column']
				if "Memory size" in metric:
					value= float(m['used'])
					print(m['column'], float(m['used']))
				else:
					value= float(m['value'])
					print(m['column'], float(m['value']))
				at_log[metric] = value
				
				continue


# parse board measurements
 #			 Total: Cycles:   74947815, Operations:  571351529, Operations/Cycle: 7.623325
# Set FC Frequency as 239616468 MHz, CL Frequency = 239616468 MHz, PERIIPH Frequency = 239616468 MHz
# Voltage: 650mV

with open(file_log, newline='') as f:
	out_log = f.readlines()
	row = []
	for line in out_log:
		if 'Set FC Frequency' in line:
#			print(line)
			parse = line.replace(',','').replace(':','').replace('=','').split()
			fre_fc = parse[4]
			fre_cl = parse[8]
			fre_pe = parse[12]
			at_log['FREQ_FC'] = fre_fc
			at_log['FREQ_CL'] = fre_cl
			at_log['FREQ_PE'] = fre_pe
			print(fre_fc,fre_cl)
#			for item in parse:	
#				print(item)
			continue
		elif 'Total' in line:
#			print(line)
			parse = line.replace(',','').replace(':','').split()
			cycles = parse[2]
			op_cycles = parse[6]
			at_log['cycles'] = cycles
			at_log['op_cycles'] = op_cycles
			print(cycles,op_cycles)
#			for item in parse:	
#				print(item)

			continue
#		for match in matches:
#			m = match.search(line)
#			if m:
#				metric = m['column']
#				value= float(m['value'])
#				at_log[metric] = value
#				print(m['column'], float(m['value']))
#				continue

print(at_log)
with open(file_name+".csv", "w", newline='') as file:
	writer = csv.writer(file, delimiter='\t')
	for item in at_log.keys():
		print(item, at_log[item])
		writer.writerow([item,at_log[item]])



