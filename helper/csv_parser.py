import glob
import csv
import pandas as pd
import numpy as np
from scipy.stats import t
import os



def calculate_ci(df):

    mean = df.mean()
    std = df.std()

    # Set confidence level
    confidence_level = 0.95

    # Compute sample size and degrees of freedom
    n = len(df)
    df = n - 1

    # Compute t-value for desired confidence level and degrees of freedom
    t_value = t.ppf((1 + confidence_level) / 2, df)

    # Compute standard error
    se = std / np.sqrt(n)

    # Compute confidence interval
    lower_ci = mean - t_value * se
    upper_ci = mean + t_value * se

    return lower_ci, upper_ci


def main():
    folders=["1UE_1018_cubic_first_100sec_DL_24prb", 
            "1UE_1018_reno_first_100sec_DL_24prb",
            "1UE_1018_vegas_first_100sec_DL_24prb",
            "1UE_1018_yeah_first_100sec_DL_24prb",
            "1UE_1018_cubic_first_100sec_UL_24prb",
            "1UE_1018_reno_first_100sec_UL_24prb",
            "1UE_1018_vegas_first_100sec_UL_24prb",
            "1UE_1018_westwood_first_100sec_UL_24prb",
            "1UE_1018_yeah_first_100sec_UL_24prb",

            "1UE_1018_cubic_first_100sec_UL_106prb",
            "1UE_1018_reno_first_100sec_UL_106prb",
            "1UE_1018_cubic_first_100sec_DL_106prb",
            "1UE_1018_reno_first_100sec_DL_106prb"
            ]

 
    for folder in folders:
        base_path = '/home/andrea/Documents/Projects/5G_measurement_framework/Data/'

        filename = '/ci_throughput_delay.csv'
        csvfilename = base_path+folder+filename
        path = base_path+folder

        tp_low = None
        tp_high = None
        rtt_low = None
        rtt_high = None
        writer = None

        # Check if the file exists
        if os.path.exists(csvfilename):
            os.remove(csvfilename)
        if not os.path.isfile(csvfilename):
            # Create a new file if it doesn't exist
            with open(csvfilename, 'w', newline='') as csvfile:
                pass  # Empty block to create an empty file


        with open(csvfilename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for i in range(1,12):
                foldername = path+str('/csv_datav')+str(i)
                
                if os.path.exists(foldername):
                    print(foldername)
                
                    files = glob.glob(os.path.join(foldername, '*.csv'))

                    if len(files) == 0:
                        print('No CSV files found in the folder')
                    else:
                        for fp in files:
                            if 'throughput.csv' in fp:
                                dfs = pd.read_csv(fp, sep=';')
                                keys = dfs.keys() 
                                lower_ci, upper_ci = calculate_ci(dfs[keys[3]])
                                tp_low = lower_ci
                                tp_high = upper_ci
                            elif 'rtt.csv' in fp and 'avg_rtt' not in fp:
                                dfs = pd.read_csv(fp, sep=';')
                                keys = dfs.keys() 
                                lower_ci, upper_ci = calculate_ci(dfs[keys[1]])
                                rtt_low = lower_ci
                                rtt_high = upper_ci

                    new_entry = [tp_low, tp_high, rtt_low, rtt_high]
                    writer.writerow(new_entry)
                else:
                    print(str(foldername) + " does not exist.")


main()