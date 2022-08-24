import numpy as np
import sys
import matplotlib.pyplot as plt
import os
import pandas as pd
import re

PLOT = True

matches = {
	"L2 Budget": re.compile(r'\s+L2 Memory size \(Bytes\)\s+: Given:\s+(?P<value>[0-9]+), Used:\s+[0-9]+\n'),
	"L2 Memory bandwidth for 1 graph run": re.compile(r'L2 Memory bandwidth for 1 graph run\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n'),
	"Percentage of baseline BW for L2": re.compile(r'Percentage of baseline BW for L2\s+\:\s+(?P<value>[0-9.]+)\s+\%\n'),
	"L3 Memory bandwidth for 1 graph run": re.compile(r'L3 Memory bandwidth for 1 graph run\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n'),
	"Percentage of baseline BW for L3": re.compile(r'Percentage of baseline BW for L3\s+\:\s+(?P<value>[0-9.]+)\s+\%\n'),
	"Tiling Bandwith overhead": re.compile(r'Tiling Bandwith overhead\s+\:\s+(?P<value>[0-9.]+)\s+Move/KerArgSize\n'),
	"Sum of all Kernels arguments size": re.compile(r'Sum of all Kernels arguments size\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n'),
	"Sum of all Kernels operations": re.compile(r'Sum of all Kernels operations\s+\:\s+(?P<value>[0-9]+)\s+Operations\n'),
	"Total amount of flash coefficients": re.compile(r'Total amount of flash coefficients\s+\:\s+(?P<value>[0-9]+)\s+Bytes\n'),
}

def main():
	l2_min = int(sys.argv[1]) if len(sys.argv) > 1 else 100
	l2_max = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
	extra_flags = sys.argv[3] if len(sys.argv) > 3 else ""

	out_dict = {n: [] for n in matches.keys()}
	for L2_MEM in range(l2_min, l2_max, 50):
		stream = os.popen(f'make clean_at_model model MODEL_L2_MEMORY={L2_MEM*1000} {extra_flags}')

		out_log = "".join(stream.readlines())
		#print(out_log)
		for name, match in matches.items():
			m = match.findall(out_log)
			if m:
				out_dict[name].append(float(m[0]))
			else:
				if name == "L2 Budget":
					out_dict[name].append(L2_MEM * 1000)
				else:
					out_dict[name].append(0.0)

	df = pd.DataFrame(out_dict)
	print(df)

	if PLOT:
		l2_budget = df["L2 Budget"].to_numpy() / 1000
		l3_bw = df["L3 Memory bandwidth for 1 graph run"].to_numpy() / 1024
		l3_bw_per = df["Percentage of baseline BW for L3"].to_numpy()

		fig, ax1 = plt.subplots()
		line1 = ax1.plot(l2_budget, l3_bw, color='red', label="L3 Memory bandwidth for 1 graph run")
		ax2 = ax1.twinx()
		line2 = ax2.plot(l2_budget, l3_bw_per, "--", color='blue', label="Percentage of baseline BW for L3")

		ax1.set_xlabel('L2 MEM [KB]', fontweight ='bold')
		ax1.set_ylabel('KB')
		ax2.set_ylabel('%')
		lns = line1 + line2
		labs = [l.get_label() for l in lns]
		ax1.legend(lns, labs, loc=0)
		plt.show()


if __name__ == "__main__":
	main()
