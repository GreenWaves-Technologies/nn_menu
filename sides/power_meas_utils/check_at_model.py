import os
import csv
import sys
import numpy as np
import pickle
import re

if len(sys.argv) != 2:
    print("Wrong number of arguments!")
    exit(1)

file_at = str(sys.argv[1])

with open(file_at, newline='') as f:
	out_log = f.readlines()
	row = []
	for line in out_log:
		if 'Execution aborted' in line:
			print('Detected')
			sys.exit(1)

sys.exit(0)
