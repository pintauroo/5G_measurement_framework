#!/bin/bash

#Add route to UE
route add -net 12.1.1.0/24 gw 192.168.70.134 dev demo-oai

#Set default values
dst_port=10000
dst_addr=12.1.1.151
frequency=0.1 #cc collection frequency
cc=cubic
DL=false #Default to UL configuration
interface=demo-oai #Interface on which packets are captured
iperf_duration=100s
srv_num=1
cli_num=1

# Parse command line arguments
while getopts ":p:a:f:c:d:i:t:" opt; do
  case $opt in
    p) dst_port=$OPTARG ;;
    a) dst_addr=$OPTARG ;;
    f) frequency=$OPTARG ;;
    c) cc=$OPTARG ;;
    d) DL=$OPTARG ;;
    i) interface=$OPTARG ;;
    t) iperf_duration=$OPTARG ;;
    \?) echo "Invalid option -$OPTARG" >&2 ;;
  esac
done

echo "Capturing on $interface"

if ! (tmux has-session -t "iperf_capture") #Avoid duplicating packet capture tmux session as this is unnecessary 
  then
    if "$DL" #Start one tmux session per SRN to capture packets on respective interface
      then
        tmux new-session -d -s "iperf_capture" 'tcpdump -i '"$interface"' -n tcp -s 88 -w 'core_DL.pcap'; sleep 0.00001' 
	echo "Dumping iperf session data in core_DL.pcap"
    else
      tmux new-session -d -s "iperf_capture" 'tcpdump -i '"$interface"' -n tcp -s 88 -w 'core_UL.pcap'; sleep 0.00001'
      echo "Dumping iperf session data in core_UL.pcap"
    fi
fi

if "$DL" #DL case
  then
    echo "dst_port: $dst_port"
    echo "dst_addr: $dst_addr"
    echo "cc frequency: $frequency"
    echo "cc alg: $cc"
    echo "iperf duration: $iperf_duration"
    echo "downlink"

    while true; do #start_data_collection_core.sh can be run multiple times on a single SRN, so ensure that tmux sessions and file names are given unique names for each run
      if ! (tmux has-session -t "iperf_client${cli_num}")
        then
	  tmux new-session -d -s "cc${cli_num}" './ss_script.sh '"$dst_addr"' '"$frequency"' > '"core_${cc}_${dst_addr}_${dst_port}_DL_client${cli_num}_v1"'; sleep 0.00001'	
          sleep 1s
	  echo "Dumping cc data in core_${cc}_${dst_addr}_${dst_port}_DL_client${cli_num}_v1"
	  tmux new-session -d -s "iperf_client${cli_num}" iperf3 -c "$dst_addr" -t "$iperf_duration" -C "$cc" -p "$dst_port"
          date +%H%M%S.%6N #Print current time for synchronization with wireless metrics
          break
      fi
      let "cli_num=cli_num+1" 
    done

    while tmux has-session -t "iperf_client${cli_num}"; do #Wait until iperf3 session ends
      sleep 5s
    done
    tmux kill-session -t "cc${cli_num}" #After iperf3 session ends, kill iperf3 client tmux session

else #UL case
  while true; do #start_data_collection_core.sh can be run multiple times on a single SRN, so ensure that tmux sessions and file names are given unique names for each run
      if ! (tmux has-session -t "iperf_server${srv_num}")
        then
          tmux new-session -d -s "iperf_server${srv_num}" iperf3 -s -p "$dst_port"
          break
      fi
      let "srv_num=srv_num+1"
  done

fi
