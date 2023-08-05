import csv
import pandas as pd
import matplotlib.pyplot as plt
import tikzplotlib

from matplotlib.lines import Line2D


def tikzplotlib_fix_ncols(obj):
    """
    workaround for matplotlib 3.6 renamed legend's _ncol to _ncols, which breaks tikzplotlib
    """
    if hasattr(obj, "_ncols"):
        obj._ncol = obj._ncols
    for child in obj.get_children():
        tikzplotlib_fix_ncols(child)



basepath = '/home/andrea/Documents/Projects/5G_measurement_framework/Data/'


folder_list = []

# UL 24prb
folders = ['1UE_1018_cubic_first_100sec_UL_24prb',
           '1UE_1018_reno_first_100sec_UL_24prb',
           '1UE_1018_vegas_first_100sec_UL_24prb',
           '1UE_1018_yeah_first_100sec_UL_24prb',
           '1UE_1018_westwood_first_100sec_UL_24prb']

folder_list.append(folders)

# # DL 24prb
folders = ["1UE_1018_cubic_first_100sec_DL_24prb",
           "1UE_1018_reno_first_100sec_DL_24prb",
           "1UE_1018_vegas_first_100sec_DL_24prb",
           "1UE_1018_yeah_first_100sec_DL_24prb"]

folder_list.append(folders)

# # # # UL 106prb
# folders = ["1UE_1018_cubic_first_100sec_UL_106prb",
#            "1UE_1018_reno_first_100sec_UL_106prb"]
# folder_list.append(folders)

# # DL 106prb
folders = ["1UE_1018_cubic_first_100sec_DL_106prb",
           "1UE_1018_reno_first_100sec_DL_106prb"]

folder_list.append(folders)

filename = '/ci_throughput_delay.csv'

# Create a figure and axes

labels = []
fsize = 26
for folders in folder_list:
    fig, ax = plt.subplots()

    for i, folder in enumerate(folders):
        # Read the CSV file
        df = pd.read_csv(basepath + folder + filename, header=None)
        x_low = df[0]  / (1024 * 1024)  # to MB
        x_high = df[1]  / (1024 * 1024)  # to MB
        y_low = df[2] 
        y_high = df[3]#

        # print(y_low)
        # print(y_high)

        # Calculate the x and y values for the plot
        x = (x_low + x_high) / 2
        y = (y_low + y_high) / 2
        x_err = (x_high - x_low) / 2
        y_err = (y_high - y_low) / 2




        if 'cubic' in folder:
            col = 'blue'
            # labels.append(plt.Line2D([], [], color=col, label='cubic'))
        elif 'reno' in folder:
            col = 'green'
            # labels.append(plt.Line2D([], [], color=col, label='reno'))
        elif 'vegas' in folder:
            col = 'red'
            # labels.append(plt.Line2D([], [], color=col, label='vegas'))
        elif 'yeah' in folder:
            col = 'pink'
            # labels.append(plt.Line2D([], [], color=col, label='yeah'))
        elif 'westwood' in folder:
            col = 'orange'
            # labels.append(plt.Line2D([], [], color=col, label='westwood'))



        markers = ['x', 'D', 'v', 'o']  # List of marker styles
        # ax.errorbar(x, y, xerr=x_err, yerr=y_err, fmt=markers[i % len(markers)], ecolor=col, capsize=10, color=col)
        ax.errorbar(x, y, xerr=x_err, yerr=y_err, fmt=markers[i % len(markers)], ecolor=col, capsize=10, markersize=5 , color=col)



    ax.set_xlabel('Throughput [Mbps]', fontsize=fsize)
    ax.set_ylabel('RTT [ms]', fontsize=fsize)

    # Increase the tick label size for both axes
    ax.tick_params(axis='both', labelsize=fsize)


    # labels = []

    # col = 'blue'
    # labels.append(Line2D([0], [0], color=col, label='cubic'))
    # col = 'green'
    # labels.append(Line2D([0], [0], color=col, label='reno'))
    # col = 'red'
    # labels.append(Line2D([0], [0], color=col, label='vegas'))
    # col = 'pink'
    # labels.append(Line2D([0], [0], color=col, label='yeah'))
    # col = 'orange'
    # labels.append(Line2D([0], [0], color=col, label='westwood'))

    # plt.legend(handles=labels, loc='center left', fontsize=fsize)


    # # Call the workaround function after creating the legend
    # tikzplotlib_fix_ncols(ax.get_legend())




    if '106' in folder:
        if 'DL' in folder:
            plt.savefig('fig1_DL_106prb.eps', format='eps', bbox_inches='tight', dpi=900)
            tikzplotlib.save("tikzfig1_DL_106prb.tex")

        else:
            plt.savefig('fig1_UL_106prb.eps', format='eps', bbox_inches='tight', dpi=900)
            tikzplotlib.save("tikzfig1_UL_106prb.tex")


    if '24' in folder:
        if 'DL' in folder:
            tikzplotlib.save("tikzfig1_DL_24prb.tex")
            plt.savefig('fig1_DL_24prb.eps', format='eps', bbox_inches='tight', dpi=900)
        else:    
            # plt.savefig('fig1_UL_24prb.pdf', bbox_inches='tight', dpi=900)
            plt.savefig('fig1_UL_24prb.eps', format='eps', bbox_inches='tight', dpi=900)
            tikzplotlib.save("tikzfig1_UL_24prb.tex")




