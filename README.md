# 5G_measurement_framework

data collection:

    tcpdump -i interface_name -n tcp -s 88


Metrics to colelct:

    1 Time-stamp (tcp jiffies)
    2 Congestion Window Size (cwnd) [packets]
    3 Round Trip Time (RTT) [ms]
    4 RTT variation between two consecutive samples [ms]
    5 Maximum Segment Size (MSS) [bytes]
    6 Number of delivered packets
    7 Packets lost during a transport session
    8 Current packets in-flight
    9 Number of retransmissions 