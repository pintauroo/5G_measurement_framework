# Hercules: An Emulation-Based Framework for Transport Layer Measurements over 5G Wireless Networks
Hercules represents a comprehensive end-to-end transport protocol analysis tool designed specifically for evaluating TCP Congestion Control performance across 5G channels. This tool has the capability to thoroughly scrutinize TCP-based internet traffic. By utilizing two pcap files – one from the source and another from the destination – Hercules extracts distinctive measurements on a per-flow basis. These measurements encompass parameters such as Sending Rate, Throughput, Fairness, Number of Retransmissions, Round-Trip Time (RTT), Average RTT, Inflight Data, and Congestion Window Size.

In order to amass measurements from the 5G protocol stack, we distribute the software within a containerized package named FILE.tar.gz. Once the measurements have been acquired, the pertinent information becomes accessible.


### Dataset collection
To make our framework as accessible as possible, we outline the general steps to conduct a basic experiment below. 

Make a reservation via the Colosseum GUI.
    Select one OAI-CORE image.
    Select the appropriate number of OAI-RAN images; at least two (one for gNB and one for each UE in the experiment).
    Once the reservation starts, ssh into the LXCs.
    Start the RF Scenario using ./start_scenario.sh, providing the scenario name as an argument; this script is located in OAI-CORE and OAI-RAN and can be started from any of the LXCs.
    
Start the core using ./start_core.sh in the OAI-CORE LXC container.
Start the gNB using ./start_gnb.sh in the OAI-RAN LXC container that has been selected to operate as the gNB.
Start the UE using ./start_ue.sh in all OAI-RAN LXC containers that have been chosen to host UEs.

Run the start_data_collection scripts in the core and UE, providing the necessary arguments; open a new terminal for the UE. Always run this script at the server side first (i.e., at the core network for UL, or at the UE for DL).  These scripts will start separate tmux sessions containing the iperf3 server and tcpdump at the server side; and the iperf3 client, tcpdump, and the CC collection script at the client side.

Once the session ends, run tmux kill-server in all terminals where the start_data_collection scripts were run.
MAC-layer data is logged in OAI-Colosseum/nr_stats.csv and end-to-end data is stored in files in the current directory (i.e., root).
When the experiment is completed, you can stop the core network using ./stop_core.sh located in OAI-CORE, and the RF scenario in any of the LXCs using ./stop_scenario.sh.

You will very likely experience lates (i.e., LLLLLL) in the gNB and UE consoles when running experimental iperf3 sessions, but this does not usually cause serious issues in our experience; especially when using 24 PRBs. In the case that the UE gets disconnected from the gNB, simply restart the UE.


### Analysis tool

The pcap parser is designed to take the pcap file from both the sender and the receiver as its input. It effectively extracts the aforementioned metrics and stores them in a CSV format, subsequently generating visual plots that depict the values over time. To execute the tool, run the following command:
```python
python pcap_parser.py
```
Contained within the Data folder are the outcomes derived from the research paper. For each type of experiment, the execution was repeated 10 times. 
We have also made available the corresponding PDF plots showcasing temporal trends and the associated CSV result files. Notably, there exists a script named __analyze.sh__ that automates the process of running the analysis across a series of replicated experiments.

