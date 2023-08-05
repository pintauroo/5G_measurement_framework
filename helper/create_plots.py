import numpy as np
import os
import errno
import math
import sys
from matplotlib.ticker import ScalarFormatter
import re
import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from helper.pcap_data import PcapData
from helper import PLOT_PATH, PLOT_TYPES
from helper.util import print_line
from helper import TEXT_WIDTH

PLOT_TOTAL = True


class Plot:
    def __init__(self, data, plot_function, file_name, plot_name, unit, number):
        self.data = data
        self.plot_function = plot_function
        self.file_name = file_name
        self.plot_name = plot_name
        self.unit = unit
        self.number = number


def plot_all(path, pcap_data, plot_only, hide_total=False, all_plots=False):

    global PLOT_TOTAL
    PLOT_TOTAL = not hide_total

    # path = os.path.join(path, PLOT_PATH)

    # if not os.path.exists(path):
    #     try:
    #         os.makedirs(path)
    #     except OSError as exc:  # Guard against race condition
    #         if exc.errno != errno.EEXIST:
    #             raise

    pcap_data = shift_timestamps(pcap_data)

    throughput = pcap_data.throughput
    fairness = pcap_data.fairness
    rtt = pcap_data.rtt
    inflight = pcap_data.inflight
    avg_rtt = pcap_data.avg_rtt
    sending_rate = pcap_data.sending_rate
    bbr_values = pcap_data.bbr_values
    bbr_total_values = pcap_data.bbr_total_values
    cwnd_values = pcap_data.cwnd_values
    retransmissions = pcap_data.retransmissions
    retransmissions_interval = pcap_data.retransmissions_interval
    buffer_backlog = pcap_data.buffer_backlog
    wireless_data = pcap_data.wireless_data

    t_max = pcap_data.get_max_ts()
    t_min = pcap_data.get_min_ts()
    plots = []

    if 'sending_rate' in plot_only:
        plots += [
            Plot((sending_rate, retransmissions), plot_sending_rate, 'plot_sending_rate.pdf', 'Sending Rate', 'bit/s', len(sending_rate))
        ]

    if 'throughput' in plot_only:
        plots += [
            Plot((throughput, retransmissions), plot_throughput, 'plot_throughput.pdf', 'Throughput', 'bit/s', len(throughput))
        ]

    if 'fairness' in plot_only and len(sending_rate.keys()) > 2:
        plots += [
            Plot(fairness, plot_fairness, 'plot_fairness.pdf', 'Fairness', "Jain's Index", len(fairness))
        ]

    if 'retransmission' in plot_only:
        plots += [
            Plot(retransmissions_interval, plot_retransmissions, 'plot_retransmissions.pdf', 'Retran.', '#', len(retransmissions_interval)),
            # Plot(retransmissions_interval, plot_retransmission_rate, 'plot_retransmission_rate.pdf', 'Retran Rate', '%', 1),
        ]

    if 'avg_rtt' in plot_only:
        plots += [
            Plot(avg_rtt, plot_avg_rtt, 'plot_avg_rtt.pdf', 'Avg RTT', 'ms', len(avg_rtt))
        ]

    if 'rtt' in plot_only:
        plots += [
            Plot(rtt, plot_rtt, 'plot_rtt.pdf', 'RTT', 'ms', len(rtt))
        ]

    if 'inflight' in plot_only:
        plots += [
            Plot(inflight, plot_inflight, 'plot_inflight.pdf', 'Inflight', 'bit', len(inflight))
        ]

    if 'cwnd' in plot_only:
        plots += [
            Plot(cwnd_values, plot_cwnd, 'plot_cwnd.pdf', 'CWnd', 'MSS', 2)
        ]

    if 'buffer_backlog' in plot_only and len(buffer_backlog) > 0:
        plots += [
            Plot((buffer_backlog, retransmissions), plot_buffer_backlog, 'plot_buffer_backlog.pdf', 'Buffer Backlog', 'bit', len(buffer_backlog))
        ]

    has_bbr = False
    if bbr_values:
        for i in bbr_values:
            if len(bbr_values[i][0]) > 0:
                has_bbr = True
                break

    if 'bdp' in plot_only and has_bbr:
        plots += [
            Plot(bbr_values, plot_bbr_bdp, 'plot_bbr_bdp.pdf', 'BDP', 'bit', len(bbr_values)),
            # Plot((inflight, bbr_values), plot_diff_inflight_bdp, 'plot_inflight_div_bdp.pdf', 'Inflight/BDP', ''),
        ]

    if 'btl_bw' in plot_only and has_bbr:
        plots += [
            Plot((bbr_values, bbr_total_values), plot_bbr_bw, 'plot_bbr_bw.pdf', 'BtlBw', 'bit/s', len(bbr_values)),
        ]

    if 'rt_prop' in plot_only and has_bbr:
        plots += [
            Plot(bbr_values, plot_bbr_rtt, 'plot_bbr_rtt.pdf', 'RTprop', 'ms', len(bbr_values)),
        ]

    if 'window_gain' in plot_only and has_bbr:
        plots += [
            Plot((bbr_values, bbr_total_values), plot_bbr_window, 'plot_bbr_window.pdf', 'Window Gain', '', len(bbr_values)),
        ]

    if 'pacing_gain' in plot_only and has_bbr:
        plots += [
            Plot((bbr_values, bbr_total_values), plot_bbr_pacing, 'plot_bbr_pacing.pdf', 'Pacing Gain', '', len(bbr_values))
        ]

    if 'wireless' in plot_only:
        plots += [
            Plot(wireless_data, wireless, 'rsrp.pdf', 'RSRP', 'dBm', 1)
        ]
        plots += [
            Plot(wireless_data, wireless_bler, 'bler.pdf', 'BLER', '%', 1)
        ]
        plots += [
            Plot(wireless_data, wireless_mcs, 'mcs.pdf', 'MCS', '', 1)
        ]
        


    f, axarr = plt.subplots(len(plots), sharex=True)

    if len(plots) == 1:
        axarr = [axarr]

    pdf_height = 14.0 * float(len(plots)) / len(PLOT_TYPES)
    f.set_size_inches(6, pdf_height)
    max_legend_rows = 1

    for i, plot in enumerate(plots):
        print_line('     -  Complete plot: {} ...'.format(plot.plot_name).ljust(TEXT_WIDTH))
        label = plot.plot_name
        if plot.unit != '':
            label += ' in {}'.format(plot.unit)

        title = '{}. {}'.format(i + 1, plot.plot_name)
        # setup_ax(ax=axarr[i], title=title, label=label, xmin=t_min, xmax=t_max)
        ax=axarr[i]
        title=title
        label=label
        xmin=t_min
        xmax=t_max
        grid_tick_maior_interval = 10
        grid_tick_minor_interval = 5

        ax.set_xticks(np.arange(xmin, xmax, grid_tick_maior_interval))
        # ax.tick_params(axis='x', labelsize=22)  # Set the x label size

        ax.set_xticks(np.arange(xmin, xmax, grid_tick_minor_interval), minor=True)
        # ax.tick_params(axis='y', labelsize=22)  # Set the y label size

        # ax.grid(which='both', color='black', linestyle='dashed', alpha=0.4)

        # ax.set_title(title)
        ax.set_xlim(left=xmin, right=xmax)
        ax.yaxis.get_offset_text().set_visible(False)

        # Set a margin for the y-axis limits
        margin = 5

        # # Calculate the new y-axis limits
        # y_min = min(y) - margin
        # y_max = max(y) + margin

        # # Set the y-axis limits with the margin
        # ax.set_ylim(y_min, y_max)
        # ax.xaxis.set_ticks_position('bottom')


        # print(axarr[i].yaxis.get_major_formatter().get_offset())

        # axarr[i].yaxis.get_offset_text().set_visible(False)
        # if 'CWnd' in label:
        #     print(i)
        #     print(len(plots)-1)
        #     axarr[i].set_xticklabels([])
        plot.plot_function(plot.data, axarr[i])


        axarr[i].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        f.canvas.draw()
        offset = axarr[i].yaxis.get_major_formatter().get_offset()
        # ax.yaxis.set_label_coords(-0.1, 0.5 * pdf_height)
        label =str(label)+ ' ' + str(offset)
        y_label = re.sub(r'\s+(?=in)', '\n', label)

        ax.set_ylabel(y_label)
        ax.set_xlabel('timeslot in seconds')

        # Set the y-label as multiple lines
       



        # print(offset)

        # legend_offset = -0.04
        # if i == len(plots) - 1:
        #     legend_offset = -0.08
        # legend = axarr[i].legend(loc='upper left', bbox_to_anchor=(0, legend_offset, 1, 0),
        #                          borderaxespad=0, ncol=20,shadow=True, fancybox=True, mode='expand')

        # max_legend_rows = max(max_legend_rows, math.ceil(plot.number / 20.0))

    print_line('  *  Complete plot ...'.ljust(TEXT_WIDTH))
    # plt.tight_layout(h_pad=-1)
    plt.tight_layout(h_pad=0)
    # plt.tight_layout(h_pad=1 + 1.5 * max_legend_rows)
    plt.savefig(os.path.join(path, 'plot_complete'+str((sys.argv[5]))+'.pdf'), dpi=1200)
    # plt.savefig(os.path.join(path, 'plot_complete'+str((sys.argv[4]))+'.pdf'), bbox_extra_artists=(legend, ), bbox_inches='tight')
    plt.savefig('plot_complete'+str((sys.argv[5]))+'.eps', format='eps', bbox_inches='tight')

    plt.close()
    print('  *  Complete plot created'.ljust(TEXT_WIDTH))

    return pcap_data


def setup_ax(ax, title , label, xmin, xmax):
    grid_tick_maior_interval = 10
    grid_tick_minor_interval = 2

    ax.set_xticks(np.arange(xmin, xmax, grid_tick_maior_interval))
    # ax.tick_params(axis='x', labelsize=22)  # Set the x label size

    ax.set_xticks(np.arange(xmin, xmax, grid_tick_minor_interval), minor=True)
    # ax.tick_params(axis='y', labelsize=22)  # Set the y label size

    # ax.grid(which='both', color='black', linestyle='dashed', alpha=0.4)

    ax.set_ylabel(label)
    # ax.set_title(title)
    ax.set_xlim(left=xmin, right=xmax)
    ax.yaxis.get_offset_text().set_visible(False)



def plot_throughput(data, p_plt):
    throughput = data[0]
    retransmissions = data[1]
    total = len(throughput) - 1

    if total > 1 and PLOT_TOTAL:
        data = throughput['total']
        data = filter_smooth(data, 5, 2)
        p_plt.plot(data[0], data[1], label='Total', color='#444444')

    for c in throughput:
        # print(c)
        data = throughput[c]
        data = filter_smooth(data, 5, 2)

        if c != 'total':
            if 10000 in c:
                col = 'blue'
            else:
                col = 'orange'
            p_plt.plot(data[0], data[1], label='{}'.format(c), color=col)

    for c in retransmissions:
        data = retransmissions[c]
        p_plt.plot(data, np.zeros_like(data), '.', color='red')


def plot_sending_rate(data, p_plt):
    sending_rate = data[0]
    retransmissions = data[1]
    total = len(sending_rate) - 1
    orange_patch = None
    blue_patch = None

    if total > 1 and PLOT_TOTAL:
        data = sending_rate['total']
        data = filter_smooth(data, 5, 2)
        p_plt.plot(data[0], data[1], label='Total', color='#444444')
    for c in sending_rate:
        data = sending_rate[c]
        data = filter_smooth(data, 5, 2)

        

        if c != 'total':
            # for custom lables change it manually
            col = 'blue'
            
            #USE THIS FOR SINGLE FLOW
            # l=''
            # if 'cubic' in sys.argv[5]:
            #     l='cubic'
            # elif 'reno' in sys.argv[5]:
            #     l='reno'
            # elif 'yeah' in sys.argv[5]:
            #     l='yeah'
            # elif 'vegas' in sys.argv[5]:
            #     l='vegas'
            # elif 'westwood' in sys.argv[5]:
            #     l='westwood'
            # blue_patch = plt.Line2D([], [], color='blue', label=l)
            
            #USE THIS FOR DOUBLE FLOW
            if 10000 in c:
                col = 'blue'
                blue_patch = plt.Line2D([], [], color='blue', label='cubic')
            else:
                col = 'orange'
                orange_patch = plt.Line2D([], [], color='orange', label='reno')


            p_plt.plot(data[0], data[1], label='{}'.format(c), color=col)

    for c in retransmissions:
        data = retransmissions[c]
        p_plt.plot(data, np.zeros_like(data), '.', color='red')

        
    if orange_patch is not None:
        legend_elements = [blue_patch, orange_patch]
        p_plt.legend(handles=legend_elements, loc='upper right', ncol=2, bbox_to_anchor=(1, 1.1))
    else:
        p_plt.legend(handles=[blue_patch], loc='best')






def plot_fairness(fairness, p_plt):


    for c in fairness:
        if c == 'Throughput':
            col = 'pink'
            blue_patch = plt.Line2D([], [], color='pink', label='Throughput')
        else:
            col = 'purple'
            orange_patch = plt.Line2D([], [], color='purple', label='Sending Rate')

        data = filter_smooth((fairness[c][0], fairness[c][1]), 10, 2)
        p_plt.plot(data[0], data[1], label=c, color=col)

    p_plt.set_ylim(bottom=0, top=1.1)
    legend_elements = [blue_patch, orange_patch]
    p_plt.legend(handles=legend_elements, loc='best', ncol=2)


def plot_rtt(rtt, p_plt):
    for c in rtt:
        if 10000 in c:
            col = 'blue'
        else:
            col = 'orange'
        data = rtt[c]
        p_plt.plot(data[0], data[1], label='{}'.format(c), color=col)
    p_plt.set_ylim(bottom=0)


def plot_avg_rtt(avg_rtt, p_plt):
    for c in avg_rtt:
        if 10000 in c:
            col = 'blue'
        else:
            col = 'orange'
        data = avg_rtt[c]
        data = filter_smooth(data, 3, 2)
        p_plt.plot(data[0], data[1], label='{}'.format(c), color=col)
    p_plt.set_ylim(bottom=0)


def plot_inflight(inflight, p_plt):
    for c in inflight:
        if 10000 in c:
            col = 'blue'
        else:
            col = 'orange'
        data = inflight[c]
        data = filter_smooth(data, 5, 1)
        p_plt.plot(data[0], data[1], label='{}'.format(c), color=col)


def plot_buffer_backlog(data, p_plt):
    buffer_backlog = data[0]
    retransmissions = data[1]
    for c in buffer_backlog:
        data = buffer_backlog[c]

        if len(data[0]) < 1:
            continue
        data = filter_smooth(data, 5, 2)
        p_plt.plot(data[0], data[1], label='Buffer Backlog {}'.format(c))

    for c in retransmissions:
        data = retransmissions[c]
        p_plt.plot(data, np.zeros_like(data), '.', color='red')


def plot_bbr_bw(data, p_plt):
    bbr = data[0]
    bbr_bw_total = data[1]

    num_flows = 0
    for c in bbr:
        data = bbr[c]
        p_plt.plot(data[0], data[1], label='{}'.format(c))
        if len(data[0]) > 0:
            num_flows += 1

    if len(bbr) > 2 and num_flows > 1 and PLOT_TOTAL:
        p_plt.plot(bbr_bw_total[0][0], bbr_bw_total[0][1], label='Total', color='#444444')


def plot_bbr_rtt(bbr, p_plt):
    for c in bbr:
        data = bbr[c]
        p_plt.plot(data[0], data[2], label='{}'.format(c))


def plot_bbr_pacing(data, p_plt):
    bbr, total = data
    for c in bbr:
        data = bbr[c]
        p_plt.plot(data[0], data[3], label='{}'.format(c))
    #if len(bbr) > 1:
    #    p_plt.plot(total[2][0], total[2][1], label='Total', color='#444444')


def plot_bbr_window(data, p_plt):
    bbr, total = data
    num_flows = 0
    for c in bbr:
        data = bbr[c]
        p_plt.plot(data[0], data[4], label='{}'.format(c))
        if len(data[0]) > 0:
            num_flows += 1
    if len(bbr) > 2 and num_flows > 1 and PLOT_TOTAL:
        p_plt.plot(total[1][0], total[1][1], label='Total', color='#444444')


def plot_bbr_bdp(bbr, p_plt):
    # print(bbr)
    for c in bbr:
        data = bbr[c]
        # print(data[0])
        p_plt.plot(data[0], data[5], label='{}'.format(c))


def plot_cwnd(cwnd, p_plt):

    for i, t in enumerate(cwnd):
        data = cwnd[t]['cwnd_values']
        # colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        if 10000 in t:
            col = 'blue'
        else:
            col = 'orange'

        p_plt.plot(data[0], data[1], color=col)
        p_plt.plot(data[0], data[2], ':', color=col)

    p_plt.plot([], [], label='CWND', color='black')
    p_plt.plot([], [], ':', label='SSTHRES', color='black')
    p_plt.legend(ncol=2)
        


def plot_retransmissions(ret_interval, p_plt):
    plot_sum = (ret_interval['total'][0][:],
                ret_interval['total'][1][:])
    total_sum = 0
    for c in ret_interval:

        if c == 'total':
            continue

        if 10000 in c:
            col = 'blue'
        else:
            col = 'orange'

        data = ret_interval[c]
        total_loss = int(sum(data[1]))
        total_sum += total_loss
        p_plt.bar(plot_sum[0], plot_sum[1], plot_sum[0][1], label=total_loss, color=col)
        for i, value in enumerate(data[0]):
            if value in plot_sum[0]:
                plot_sum[1][plot_sum[0].index(value)] -= data[1][i]

    p_plt.bar(plot_sum[0], plot_sum[1], plot_sum[0][1], label='Total {}'.format(total_sum), color='black')


def plot_retransmission_rate(ret_interval, p_plt):

    for c in ret_interval:

        data = ret_interval[c]

        rate = []
        ts = data[0]

        for i,_ in enumerate(data[1]):
            if data[2][i] == 0:
                rate.append(0)
            else:
                rate.append(float(data[1][i]) / float(data[2][i]) * 100)

        if c == 'total':
            p_plt.plot(ts, rate, label='Total Retransmission Rate', color='black')
        else:
            if 10000 in c:
                col = 'blue'
            else:
                col = 'orange'
            p_plt.plot(ts, rate, label='{}'.format(c), alpha=0.3, color=col)

    p_plt.set_ylim(bottom=0)


def plot_diff_inflight_bdp(data, p_plt):
    inflight = data[0]
    bbr = data[1]
    for c in inflight:

        if c not in bbr:
            continue

        ts = []
        diff = []

        bbr_ts = bbr[c][0]
        bdp = bbr[c][5]

        for i, t1 in enumerate(inflight[c][0]):
            for j, t2 in enumerate(bbr_ts):
                if t1 > t2:
                    ts.append(t2)
                    if bdp[j] == 0:
                        diff.append(0)
                    else:
                        diff.append((inflight[c][1][i]) / bdp[j])
                else:
                    bbr_ts = bbr_ts[j:]
                    bdp = bdp[j:]
                    break
        ts, diff = filter_smooth((ts, diff), 10, 5)
        p_plt.plot(ts, diff, label='{}'.format(c))


def filter_smooth(data, size, repeat=1):
    x = data[0]
    y = data[1]

    if repeat == 0:
        return x, y

    size = int(math.ceil(size / 2.0))
    for _ in range(1, repeat):
        y_smooth = []
        for i in range(0, len(y)):
            avg = 0
            avg_counter = 0
            for j in range(max(0, i - size), min(i + size, len(y) - 1)):
                avg += y[j]
                avg_counter += 1
            if avg_counter > 0:
                y_smooth.append(avg / avg_counter)
            else:
                y_smooth.append(0)
        y = y_smooth
    return x, y


def filter_percentile(data, percentile_min=0.0, percentile_max=0.0):
    min_size = int(math.floor(percentile_min * len(data[0])))
    max_size = int(math.floor(percentile_max * len(data[0])))

    y, x = zip(*sorted(zip(data[1], data[0])))
    if max_size > 0:
        x = x[min_size:-max_size]
        y = y[min_size:-max_size]
    else:
        x = x[min_size:]
        y = y[min_size:]

    x, y = zip(*sorted(zip(x, y)))

    return x, y


def shift_timestamps(data):
    t_min = data.get_min_ts()
    t_max = data.get_max_ts()
    maxtime = t_max-t_min
    # print(t_min)
    data = data.values_as_dict()


    for v in data:
        # print(v)
        if v == 'cwnd_values':
            for i in data[v]:
                print(v)
                print(len(data[v][i]['cwnd_values'][0]))
                tmp = [], [], []
                tmp0=[]
                tmp1=[]
                tmp2=[]

                first=True #sync flag
                for k, x in enumerate(data[v][i]['cwnd_values'][0]):
                    if first:
                        difference = x - t_min
                        first=False
                        print('sec difference: ' +str(difference))

                    tstamp = x - t_min - difference

                    if 0 <= tstamp <= maxtime:
                        tmp0.append(tstamp)
                        tmp1.append(data[v][i]['cwnd_values'][1][k])
                        tmp2.append(data[v][i]['cwnd_values'][2][k])
                tmp = tmp0, tmp1, tmp2
                # print(len(tmp0))
                data[v][i]['cwnd_values'] = tmp
                print(len(data[v][i]['cwnd_values'][0]))

        elif v == 'wireless_data':
            if data[v] is not None:
                print(v)


                print(len(data[v][0]))
                tmp = [], []
                tmp0=[]
                tmp1=[]
                tmp2=[]
                tmp3=[]

                first=True #sync flag
                for k, x in enumerate(data[v][0]):
                    x = float(x)
                    if first:
                        difference = x - t_min
                        first=False
                        print('sec difference: ' +str(difference))

                    tstamp = x - t_min - difference

                    if 0 <= tstamp <= maxtime:
                        tmp0.append(tstamp)
                        tmp1.append(data[v][1][k])
                        tmp2.append(data[v][2][k])
                        tmp3.append(data[v][3][k])
                        # data[v][i]['cwnd_values'][0][k] = tstamp
                tmp = tmp0, tmp1, tmp2, tmp3
                # print(len(tmp0))
                data[v] = tmp
                print(data[v][0])
            
        elif data[v] is not None:
             for c in data[v]:
                data[v][c][0][:] = [x - t_min for x in data[v][c][0]]
    print('Timestamp shift')
    return PcapData.from_dict(data)


def wireless(wireless_data, p_plt):
    data = {'ts': wireless_data[0], 'rsrp': wireless_data[1]}
    df = pd.DataFrame(data)
    filtered_df = df[(df['rsrp'] >= -140) & (df['rsrp'] <= -40)]
    p_plt.plot(filtered_df['ts'], filtered_df['rsrp'], label='RSRP', color='green')
    p_plt.legend()

def wireless_bler(wireless_data, p_plt):
    data = {'ts': wireless_data[0], 'bler': wireless_data[2]}
    df = pd.DataFrame(data)
    p_plt.plot(df['ts'], df['bler']*100, label='BLER', color='green')
    p_plt.legend()

def wireless_mcs(wireless_data, p_plt):
    data = {'ts': wireless_data[0], 'mcs': wireless_data[3]}
    df = pd.DataFrame(data)
    p_plt.plot(df['ts'], df['mcs'], label='MCS', color='green')
    p_plt.legend()



