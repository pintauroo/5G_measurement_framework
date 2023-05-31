import dpkt
import socket
import sys

import re

import matplotlib.pyplot as plt

from helper.pcap_data import PcapData
from helper.create_plots import plot_all
from helper.util import check_directory, print_line, open_compressed_file, colorize, get_ip_from_filename, get_interface_from_filename
from helper.csv_writer import write_to_csv, read_from_csv



delta_t = 0.2




# to merge: mergecap -F pcap -w merged.pcap ue2_ul_reno.pcap ue1_ul_cubic.pcap

pcap1=(sys.argv[1]) #snd
pcap2=(sys.argv[2]) #rcv
cc_file=(sys.argv[3])




ports = [10000, 10001, 10002]  # list of port numbers to search for
flags = {10000: False, 10001: False, 10002: False}  # dictionary of flags, initialized to False
control_ports=[]
ips=[]



def main():
    print(pcap1)
    f = open(pcap1, 'rb')
    total_packets = len(list(dpkt.pcap.Reader(open_compressed_file(pcap1)))) + \
                    len(list(dpkt.pcap.Reader(open_compressed_file(pcap1))))
    print('  Found {} frames.'.format(colorize(total_packets, 'green')))


    processed_packets = 0

    pcap = dpkt.pcap.Reader(f)

    connections = []
    active_connections = []

    round_trips = {}
    inflight = {}
    sending_rate = {}
    avg_rtt = {}

    inflight_seq = {}
    inflight_ack = {}

    sending_rate_data_size = {}

    inflight_avg = {}

    avg_rtt_samples = {}

    total_throughput = ([], [])
    total_sending_rate = ([], [])

    retransmissions = {}
    retransmission_counter = {}
    packet_counter = {}
    retransmissions_interval = {}
    total_retransmisions = ([], [], [])

    start_seq = {}

    t = 0

    ts_vals = {}
    seqs = {}

    start_ts = -1
    first=False

    print('Connections:')

    flag1 = False
    flag2 = False

    for ts, buf in pcap:


        eth = dpkt.ethernet.Ethernet(buf)
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:
            ip = dpkt.ip.IP(buf)
        else:
            ip = eth.data


        if start_ts < 0:
            start_ts = ts
            t = start_ts + delta_t

        processed_packets += 1
        if processed_packets % 500 == 0:
            print_progress(processed_packets, total_packets)

        tcp = ip.data   

        src_ip = socket.inet_ntoa(ip.src)
        dst_ip = socket.inet_ntoa(ip.dst)
        src_port = tcp.sport
        dst_port = tcp.dport



        if src_port==80 or dst_port==80: # skip system http connections
            continue

        for port in ports:
            if (src_port==port or dst_port==port) and not flags[port]:
                control_ports.append(src_port)
                print(src_port)
                flags[port] = True

        if src_port in control_ports:
            continue


        if src_port in control_ports or dst_port in control_ports: # skip iperf control port
            continue

        # identify a connection always as (client port, server port)
        if src_port > dst_port:
            tcp_tuple = (src_ip, src_port, dst_ip, dst_port)
        else:
            tcp_tuple = (dst_ip, dst_port, src_ip, src_port)

        if src_ip not in ips:
            ips.append(src_ip)
        if dst_port not in ips:
            ips.append(dst_ip)

        if tcp_tuple not in connections and tcp.flags & 0x02 == False :
            print("skip " +str(tcp_tuple))
            continue

        while ts >= t:

            total_sending_rate[0].append(t)
            total_sending_rate[1].append(0)

            total_retransmisions[0].append(t)
            total_retransmisions[1].append(0)
            total_retransmisions[2].append(0)

            for key in connections:

                if key not in active_connections:
                    continue

                tp = float(sending_rate_data_size[key]) / delta_t
                sending_rate[key][0].append(t)
                sending_rate[key][1].append(tp)
                sending_rate_data_size[key] = 0

                total_sending_rate[1][-1] += tp

                retransmissions_interval[key][0].append(t)
                retransmissions_interval[key][1].append(retransmission_counter[key])
                retransmissions_interval[key][2].append(packet_counter[key])
                total_retransmisions[1][-1] += retransmission_counter[key]
                total_retransmisions[2][-1] += packet_counter[key]
                retransmission_counter[key] = 0
                packet_counter[key] = 0

                inflight[key][0].append(t)
                if len(inflight_avg[key]) > 0:
                    inflight[key][1].append(sum(inflight_avg[key]) / len(inflight_avg[key]))
                else:
                    inflight[key][1].append(0)
                inflight_avg[key] = []

                if len(avg_rtt_samples[key]) > 0:
                    avg_rt = sum(avg_rtt_samples[key]) / len(avg_rtt_samples[key])
                    avg_rtt[key][0].append(t)
                    avg_rtt[key][1].append(avg_rt)
                avg_rtt_samples[key] = []

            t += delta_t

        if tcp.flags & 0x02 and tcp_tuple not in connections:
            connections.append(tcp_tuple)
            active_connections.append(tcp_tuple)
            connection_index = tcp_tuple

            start_seq[connection_index] = tcp.seq

            round_trips[connection_index] = ([], [])
            inflight[connection_index] = ([], [])
            avg_rtt[connection_index] = ([], [])
            sending_rate[connection_index] = ([], [])

            ts_vals[connection_index] = ([], [])
            seqs[connection_index] = []

            inflight_seq[connection_index] = 0
            inflight_ack[connection_index] = 0

            inflight_avg[connection_index] = []

            sending_rate_data_size[connection_index] = 0

            avg_rtt_samples[connection_index] = []

            retransmissions[connection_index] = ([],)
            retransmission_counter[connection_index] = 0
            packet_counter[connection_index] = 0
            retransmissions_interval[connection_index] = ([], [], [])

            print('  [SYN] {}:{} -> {}:{}'.format(tcp_tuple[0], tcp_tuple[1],
                                                  tcp_tuple[2], tcp_tuple[3]))

        if tcp.flags & 0x01:
            if tcp_tuple in active_connections:
                first=False
                active_connections.remove(tcp_tuple)
                print('  [FIN] {}:{} -> {}:{}'.format(tcp_tuple[0], tcp_tuple[1],
                                                      tcp_tuple[2], tcp_tuple[3]))
            continue

        connection_index = tcp_tuple

        ts_val = None
        ts_ecr = None

# These TSval values are echoed in TSecr values in the reverse
# direction.  The difference between a received TSecr value and the
# current timestamp clock value provides an RTT measurement.


        options = dpkt.tcp.parse_opts(tcp.opts)
        for opt in options:
            if opt[0] == dpkt.tcp.TCP_OPT_TIMESTAMP:
                ts_val = int.from_bytes(opt[1][:4], 'big')
                ts_ecr = int.from_bytes(opt[1][4:], 'big')

        if src_port > dst_port:
            # client -> server
            tcp_seq = tcp.seq - start_seq[connection_index]
            if tcp_seq < 0:
                tcp_seq += 2 ** 32

            packet_counter[connection_index] += 1

            inflight_seq[connection_index] = max(tcp_seq, inflight_seq[connection_index])
            sending_rate_data_size[connection_index] += ip.len * 8

            if tcp_seq in seqs[connection_index]:
                retransmissions[connection_index][0].append(ts)
                retransmission_counter[connection_index] += 1

            else:
                seqs[connection_index].append(tcp_seq)
                if ts_val is not None:
                    ts_vals[connection_index][0].append(ts)
                    ts_vals[connection_index][1].append(ts_val)

        else:
            # server -> client
            tcp_ack = tcp.ack - start_seq[connection_index]
            if tcp_ack < 0:
                tcp_ack += 2 ** 32

            inflight_ack[connection_index] = max(tcp_ack, inflight_ack[connection_index])

            seqs[connection_index] = [x for x in seqs[connection_index] if x >= tcp_ack]

            if ts_ecr in ts_vals[connection_index][1]:
                index = ts_vals[connection_index][1].index(ts_ecr)
                rtt = (ts - ts_vals[connection_index][0][index]) * 1000

                ts_vals[connection_index][0].pop(index)
                ts_vals[connection_index][1].pop(index)

                avg_rtt_samples[connection_index].append(rtt)

                round_trips[connection_index][0].append(ts)
                round_trips[connection_index][1].append(rtt)

        inflight_data = max(0, inflight_seq[connection_index] - inflight_ack[connection_index])
        inflight_avg[connection_index].append(inflight_data * 8)

    f.close()



# ---------------------------------------------------------------

    f = open_compressed_file(pcap2)

    pcap = dpkt.pcap.Reader(f)

    connections = []
    active_connections = []
    throughput = {}

    throughput_data_size = {}

    t = start_ts + delta_t
    first=False
    for ts, buf in pcap:
        eth = dpkt.ethernet.Ethernet(buf)

        if eth.type != dpkt.ethernet.ETH_TYPE_IP:
            ip = dpkt.ip.IP(buf)
        else:
            ip = eth.data



        processed_packets += 1
        if processed_packets % 500 == 0:
            print_progress(processed_packets, total_packets)

        tcp = ip.data

        src_ip = socket.inet_ntoa(ip.src)
        dst_ip = socket.inet_ntoa(ip.dst)
        src_port = tcp.sport
        dst_port = tcp.dport

        # identify a connection always as (client port, server port)
        if src_port > dst_port:
            tcp_tuple = (src_ip, src_port, dst_ip, dst_port)
        else:
            tcp_tuple = (dst_ip, dst_port, src_ip, src_port)


        
        if tcp_tuple not in connections and tcp.flags & 0x02 == False :
            continue
        while ts >= t:
            total_throughput[0].append(t)
            total_throughput[1].append(0)

            for key in connections:
                if key not in active_connections:
                    continue
                tp = float(throughput_data_size[key]) / delta_t
                throughput[key][0].append(t)
                throughput[key][1].append(tp)
                total_throughput[1][-1] += tp
                throughput_data_size[key] = 0
            t += delta_t

        if tcp.flags & 0x02 and tcp_tuple not in connections:
            connections.append(tcp_tuple)

            active_connections.append(tcp_tuple)
            connection_index = tcp_tuple

            throughput[connection_index] = ([], [])
            throughput_data_size[connection_index] = 0

        if tcp.flags & 0x01:
            if tcp_tuple in active_connections:
                active_connections.remove(tcp_tuple)
            continue

        connection_index = tcp_tuple

        if src_port > dst_port:
            # client -> server
            throughput_data_size[connection_index] += ip.len * 8

    print('  100.00%')

    print(control_ports)
    # fairness_troughput = compute_fairness(throughput, delta_t)
    # fairness_sending_rate = compute_fairness(sending_rate, delta_t)
    fairness = None
    bbr_values = None
    bbr_total_values = None
    cwnd_values = None
    data_info = None
    # fairness = {
    #     'Throughput': fairness_troughput,
    #     'Sending Rate': fairness_sending_rate
    # }

    bbr_values, cwnd_values = parse_bbr_and_cwnd_values()
    # bbr_total_values, sync_phases, sync_duration = compute_total_values(bbr_values)
    # # buffer_backlog = parse_buffer_backlog(path)

    # data_info = DataInfo(sync_duration=sync_duration,
    #                      sync_phases=sync_phases)

    throughput['total'] = total_throughput
    sending_rate['total'] = total_sending_rate
    retransmissions_interval['total'] = total_retransmisions

    p = PcapData(   
                    rtt=round_trips,
                    inflight=inflight,
                    throughput=throughput,
                    fairness=fairness if fairness is not None else None,
                    avg_rtt=avg_rtt,
                    sending_rate=sending_rate,
                    bbr_values=bbr_values if bbr_values is not None else None,
                    bbr_total_values=bbr_total_values if bbr_total_values is not None else None,
                    cwnd_values=cwnd_values if bbr_values is not None else None,
                    retransmissions=retransmissions,
                    retransmissions_interval=retransmissions_interval,
                    # buffer_backlog=buffer_backlog,
                    data_info=data_info if bbr_values is not None else None
                )
    write_to_csv('.', p, compression='none')
    # print(throughput)
    # plot_all('.', p, plot_only=['sending_rate'])
    plot_all('/home/andrea/Documents/Projects/5G_measurement_framework', p, plot_only=['cwnd', 'sending_rate', 'throughput', 'retransmission', 'avg_rtt', 'rtt', 'avg_rtt', 'avg_rtt', 'inflight'])
    # plot_all('.', p, plot_only=['sending_rate', 'throughput', 'fairness', 'retransmission', 'avg_rtt', 'rtt', 'avg_rtt', 'avg_rtt', 'inflight'])
    # plot_all('.', p, plot_only=['bdp', 'btl_bw', 'rt_prop', 'window_gain', 'pacing_gain', 'sending_rate', 'throughput', 'fairness', 'retransmission', 'avg_rtt', 'rtt', 'avg_rtt', 'avg_rtt', 'inflight'])
        

def print_progress(current, total):
    print_line('  {:7.3}%          '.format(100 * current / float(total)))

def compute_fairness(data, interval):
    output = ([], [])
    connections = {k: 0 for k in data.keys()}

    max_ts = 0
    min_ts = float('inf')
    for c in data:
        max_ts = max(max_ts, max(data[c][0]))
        min_ts = min(min_ts, min(data[c][0]))

    ts = min_ts
    while True:
        if ts > max_ts:
            break

        shares = []
        for i in data.keys():
            if len(data[i][0]) <= connections[i]:
                continue
            if data[i][0][connections[i]] == ts:
                shares.append(data[i][1][connections[i]])
                connections[i] += 1

        output[0].append(ts)
        output[1].append(compute_jain_index(*shares))
        ts += interval
    return output



def compute_jain_index(*args):

    sum_normal = 0
    sum_square = 0

    for arg in args:
        sum_normal += arg
        sum_square += arg**2

    if len(args) == 0 or sum_square == 0:
        return 1

    return sum_normal ** 2 / (len(args) * sum_square)




def parse_bbr_and_cwnd_values():
   
   
    with open(cc_file, 'r') as f:
        lines = f.readlines()

    data = []

    last_ts = None
    flag=False
    cc=None
    bbr=False
    fields = {}
    bbr_values = {}
    cwnd_values = {}

    for line in lines:

        if line == '' or line == '\n': # clean white lines
            continue

        line = line.strip()

        # use regular expression to replace multiple spaces with a single space
        line = re.sub(r'\s+', ' ', line)

        # split the line into a list of values
        values = line.split(' ')

        if len(values) == 1: # save timestamp
            last_ts = line
            continue

        # remove the semicolon from the first value
        values[0] = values[0].rstrip(';')



        for p in control_ports:
            if str(p) in line:
                flag = True
                continue
        
        if flag == True:
            flag = False
            continue

        if 'State' in line:
            continue

        if "ESTAB" in line:

            fields['timestamp'] = float(last_ts)
            fields['State'] = values[0]
            fields['Recv-Q'] = values[1]
            fields['Send-Q'] = values[2]
            src_addr, src_port = values[3].split(':')
            fields['src_addr'] = src_addr
            fields['src_port'] = src_port
            dst_addr, dst_port = values[4].split(':')
            fields['dst_addr'] = dst_addr
            fields['dst_port'] = dst_port
            ip=src_addr
            if ip not in cwnd_values:
                cwnd_values[ip] = ([], [], [])

        else:
            if 'cubic' in line:
                cc = 'cubic'
                values = line.split()

                for value in values:
                    key_value = value.split(":", 1)
                    if len(key_value) == 2:
                        key = key_value[0]
                        value = key_value[1]

                        # If the value contains a slash, split it into two values
                        if "/" in value:
                            sub_values = value.split("/")
                            if 'rtt' in key:
                                fields['rtt'] = sub_values[0]
                                fields['rtt_var'] = sub_values[1]
                            else:
                                fields[key+"_min"] = sub_values[0]
                                fields[key+"_max"] = sub_values[1]
                        else:
                            fields[key] = value

            else:
                for value in values[1:]:     
                
                    if ':' in value:
                        # print(value)


                        if 'bbr' in value:
                            bbr = True

                            bbr = value.replace('bbr:(bw:', '')\
                            .replace('mrtt:','')\
                            .replace('pacing_gain:', '')\
                            .replace('cwnd_gain:', '')\
                            .replace(')', '')
                            bbr = bbr.split(',')

                            if len(bbr) < 4:
                                pacing_gain = 0
                                cwnd_gain = 0
                            else:
                                pacing_gain = float(bbr[2])
                                cwnd_gain = float(bbr[3])

                            if 'Mbps' in bbr[0]:
                                bw = float(bbr[0].replace('Mbps', '')) * 1000000
                            elif 'Gbps' in bbr[0]:
                                bw = float(bbr[0].replace('Gbps', '')) * 1000000000
                            elif 'Kbps' in bbr[0]:
                                bw = float(bbr[0].replace('Kbps', '')) * 1000
                            elif 'bps' in bbr[0]:
                                bw = float(bbr[0].replace('bps', ''))
                            else:
                                bw = 0

                            mrtt = float(bbr[1])

                            fields['bbr_bw'] = bw
                            fields['bbr_rtt'] = mrtt
                            fields['bbr_pacing_gain'] = pacing_gain
                            fields['bbr_cwnd_gain'] = cwnd_gain


                        elif 'rtt' in value and 'minrtt' not in value:
                            lable, val = value.split(":")
                            rtt, rtt_std = val.split("/")

                            fields['rtt'] = rtt
                            fields['rtt_std'] = rtt_std
                        else:
                            key, val = value.split(':')
                            fields[key] = val
                    elif 'wscale:' in value:
                        wscale = value.split(':')[1].split(',')
                        fields['wscale_left'] = int(wscale[0])
                        fields['wscale_right'] = int(wscale[1])

                    
                    

            if 'timestamp' in fields: 
                data.append(fields)
                cwnd_values[ip][0].append(float(fields['timestamp']) if 'timestamp' in fields else 0)
                cwnd_values[ip][1].append(float(fields['cwnd']) if 'cwnd' in fields else 0)
                cwnd_values[ip][2].append(float(fields['ssthresh']) if 'ssthresh' in fields else 0)

                if bbr:

                    if ip not in bbr_values:
                        bbr_values[ip] = ([], [], [], [], [], [])

                    bbr_values[ip][0].append(float(fields['timestamp']))
                    bbr_values[ip][1].append(fields['bbr_bw'])
                    bbr_values[ip][2].append(fields['bbr_rtt'])
                    bbr_values[ip][3].append(fields['bbr_pacing_gain'])
                    bbr_values[ip][4].append(fields['bbr_cwnd_gain'])
                    bbr_values[ip][5].append(fields['bbr_bw'] * fields['bbr_rtt'] / 1000)

            fields = {}
    return bbr_values, cwnd_values


def parse_timestamp(string):
    return float(string)


def compute_total_values(bbr):
    connection_first_index = {f: 0 for f in bbr}
    current_bw = {f: 0 for f in bbr}
    current_window = {f: 0 for f in bbr}
    current_gain = {f: 0 for f in bbr}

    total_bw = ([], [])
    total_window = ([], [])
    total_gain = ([], [])

    sync_window_start = -1
    sync_window_phases = []
    sync_window_durations = []

    while True:
        active_connections = 0
        current_timestamps = {}

        for c in bbr:
            if connection_first_index[c] < len(bbr[c][0]):
                current_timestamps[c] = bbr[c][0][connection_first_index[c]]
                active_connections += 1
            else:
                current_window[c] = 0
                current_bw[c] = 0
                current_gain[c] = 0

        if active_connections < 1:
            break

        c, ts = min(current_timestamps.items(), key=lambda x: x[1])
        current_bw[c] = bbr[c][1][connection_first_index[c]]
        current_window[c] = float(bbr[c][4][connection_first_index[c]])
        current_gain[c] = float(bbr[c][3][connection_first_index[c]])
        connection_first_index[c] += 1

        total_bw[0].append(ts)
        total_bw[1].append(sum(current_bw.values()))

        total_window[0].append(ts)
        total_window[1].append(sum(current_window.values()))

        total_gain[0].append(ts)
        total_gain[1].append(sum(current_gain.values()))

        min_window = 0
        for i in connection_first_index.values():
            if i > 0:
                min_window += 1

        if sum(current_window.values()) == min_window:
            if sync_window_start < 0:
                sync_window_start = ts
                sync_window_phases.append(sync_window_start)
        elif sync_window_start > 0:
            duration = (ts - sync_window_start) * 1000
            sync_window_start = -1
            sync_window_durations.append(duration)

    return {0: total_bw, 1: total_window, 2: total_gain}, sync_window_phases, sync_window_durations


def compute_fairness(data, interval):
    output = ([], [])
    connections = {k: 0 for k in data.keys()}

    max_ts = 0
    min_ts = float('inf')
    for c in data:
        max_ts = max(max_ts, max(data[c][0]))
        min_ts = min(min_ts, min(data[c][0]))

    ts = min_ts
    while True:
        if ts > max_ts:
            break

        shares = []
        for i in data.keys():
            if len(data[i][0]) <= connections[i]:
                continue
            if data[i][0][connections[i]] == ts:
                shares.append(data[i][1][connections[i]])
                connections[i] += 1

        output[0].append(ts)
        output[1].append(compute_jain_index(*shares))
        ts += interval
    return output


def compute_jain_index(*args):

    sum_normal = 0
    sum_square = 0

    for arg in args:
        sum_normal += arg
        sum_square += arg**2

    if len(args) == 0 or sum_square == 0:
        return 1

    return sum_normal ** 2 / (len(args) * sum_square)


if __name__ == "__main__":
    main()



