# Hercules: 5G_measurement_framework
Hercules represents a comprehensive end-to-end transport protocol analysis tool designed specifically for evaluating TCP Congestion Control performance across 5G channels. This tool has the capability to thoroughly scrutinize TCP-based internet traffic. By utilizing two pcap files – one from the source and another from the destination – Hercules extracts distinctive measurements on a per-flow basis. These measurements encompass parameters such as Sending Rate, Throughput, Fairness, Number of Retransmissions, Round-Trip Time (RTT), Average RTT, Inflight Data, and Congestion Window Size.

In order to amass measurements from the 5G protocol stack, we distribute the software within a containerized package named FILE.tar.gz. Once the measurements have been acquired, the pertinent information becomes accessible.


### Dataset collection
Here we describe how to 
### Analysis tool

The pcap parser is designed to take the pcap file from both the sender and the receiver as its input. It effectively extracts the aforementioned metrics and stores them in a CSV format, subsequently generating visual plots that depict the values over time. To execute the tool, run the following command:
python pcap_parser.py

Contained within the Data folder are the outcomes derived from the research paper. For each type of experiment, the execution was repeated 10 times. We have also made available the corresponding PDF plots showcasing temporal trends and the associated CSV result files. Notably, there exists a script named analyzes.sh that automates the process of running the analysis across a series of replicated experiments.
