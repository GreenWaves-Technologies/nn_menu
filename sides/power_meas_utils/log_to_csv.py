import os
from glob import glob
import pandas as pd
import sys
import re
import csv

MEAS_SETTINGS = {
    "CH_A_Avg": ["SoC Before DCDC [mW]", 1.8, 1],
    "CH_B_Avg": ["SoC After DCDC [mW]", None, 0.5],
    #"CH_C_Avg": ["Trigger", None, 0.5],
    "CH_D_Avg": ["IO [mW]", 1.8, 0.25],
}

def convert_meas_to_mW(dataframe: pd.DataFrame, settings):
    for name, setting in settings.items():
        voltage = setting[1] if setting[1] is not None else dataframe["Voltage [V]"]
        dataframe[name] = dataframe[name] * voltage / setting[2]
        dataframe = dataframe.rename(columns={name: setting[0]})
    dataframe.insert(dataframe.columns.get_loc("SoC After DCDC [mW]")+1, "Efficiency DCDC", dataframe["SoC After DCDC [mW]"] / dataframe["SoC Before DCDC [mW]"])
    dataframe.insert(dataframe.columns.get_loc("Latency [ms]")+1, "Energy [uJ]", dataframe["Latency [ms]"] * dataframe["SoC Before DCDC [mW]"])
    return dataframe

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

def main():
    matches = [L3_MEM_BW, L2_MEM_BW, TIL_OH, KER_ARGS, L2_MEM_BW_PER, L3_MEM_BW_PER, KER_OPS, TOT_COEFFS,L1_MEM_USAGE, L2_MEM_USAGE, L3_MEM_USAGE]

    if len(sys.argv) != 4:
        print("Wrong number of arguments!")
        exit(1)
    file_pow = str(sys.argv[1])
    file_at = str(sys.argv[2])
    out_file = str(sys.argv[3])

    # log file
    at_log = {}
    # parse power measurements
    with open(file_pow, newline='') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            print(row[0], float(row[1]))
            if len(row) == 2:
                at_log[row[0]] = [float(row[1])]

    # parse AT measures
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
                    at_log[metric] = [value]
                    continue
    print(at_log)
    print("--------------------")

    filename = os.path.splitext(file_pow)[0]
    model_name = filename.split("_")[1]
    freq = int(filename.split("_")[-2])
    voltage = int(filename.split("_")[-1]) / 1000
    mode = "NE16" if "NE16" in filename else ("FP16" if "FP16" in filename else "SQ8")
    mode += "_HWC" if "HWC" in filename else ""
    df = pd.DataFrame.from_dict(at_log)
    df.insert(0, "Model", model_name)
    df.insert(1, "Mode", mode)
    df.insert(1, "Frequency [MHz]", freq)
    df.insert(1, "Voltage [V]", voltage)
    df = df.sort_values(["Mode", "Voltage [V]"])
    df = df.rename(
        columns={
            "n_Points": "Latency [ms]"})
    df["Latency [ms]"] /= 1000
    total_cyc = df["Latency [ms]"] * df["Frequency [MHz]"] * 1000
    ops_over_cyc = df["Sum of all Kernels operations"] / total_cyc
    df.insert(df.columns.get_loc("Latency [ms]")+1, "Cyc", total_cyc)
    df.insert(df.columns.get_loc("Cyc")+1, "Ops/Cyc", ops_over_cyc)
    df = convert_meas_to_mW(df, MEAS_SETTINGS)
    print(df)
    if os.path.exists(out_file):
        df_before = pd.read_csv(out_file)
        df = df_before.append(df)
    df.to_csv(out_file, index=False)

if __name__ == '__main__':
    main()
