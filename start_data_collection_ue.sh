#!/bin/bash

#Add route to core
route add default gw 12.1.1.1

#Set default values
dst_port=10000
dst_addr=192.168.70.129
frequency=0.1
cc=cubic
DL=false
interface=oaitun_ue1
iperf_duration=100s
pcap_file_name=ue.pcap
cc_file_name=ue_cc

# Parse command line arguments
while getopts ":p:a:f:c:d:i:t:x:y:" opt; do
  case $opt in
    p) dst_port=$OPTARG ;;
    a) dst_addr=$OPTARG ;;
    f) frequency=$OPTARG ;;
    c) cc=$OPTARG ;;
    d) DL=$OPTARG ;;
    i) interface=$OPTARG ;;
    t) iperf_duration=$OPTARG ;;
    x) pcap_file_name=$OPTARG ;;
    y) cc_file_name=$OPTARG ;;
    \?) echo "Invalid option -$OPTARG" >&2 ;;
  esac
done

echo "Capturing on $interface"
echo "Dumping iperf session data in $pcap_file_name"

tmux new-session -d -s "iperf_capture" 'tcpdump -i '"$interface"' -n tcp -s 88 -w '"$pcap_file_name"'; sleep 0.00001' 

if "$DL"
  then
    tmux new-session -d -s "iperf_server" iperf3 -s -p "$dst_port"

else
  echo "dst_port: $dst_port"
  echo "dst_addr: $dst_addr"
  echo "cc frequency: $frequency"
  echo "cc alg: $cc"
  echo "iperf duration: $iperf_duration"
  echo "Dumping cc data in $cc_file_name"
  echo "uplink" 
  
  tmux new-session -d -s "cc" './ss_script.sh '"$dst_addr"' '"$frequency"' > '"$cc_file_name"'; sleep 0.00001'
    sleep 1s
  tmux new-session -d -s "iperf_client" iperf3 -c "$dst_addr" -t "$iperf_duration" -C "$cc" -p "$dst_port"
  date +%H%M%S.%6N
  
  while tmux has-session -t "iperf_client"; do
      sleep 10s
    done
 
    tmux kill-server

fi
