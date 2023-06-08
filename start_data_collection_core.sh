#!/bin/bash

#Add route to UE
route add -net 12.1.1.0/24 gw 192.168.70.134 dev demo-oai

#Set default values
dst_port=10000
dst_addr=12.1.1.151
frequency=0.1
cc=cubic
DL=false
interface=demo-oai
iperf_duration=100s
tcpdump_tmux_name=iperf_capture
cc_tmux_name=cc
iperf_client_tmux_name=iperf_client
iperf_server_tmux_name=iperf_server
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
echo "Dumping iperf session data in $pcap_file_name"

if ! (tmux has-session -t "$iperf_capture")
  then
    if "$DL"
      then
        tmux new-session -d -s "iperf_capture" 'tcpdump -i '"$interface"' -n tcp -s 88 -w 'core_DL.pcap'; sleep 0.00001' 
    else
      tmux new-session -d -s "iperf_capture" 'tcpdump -i '"$interface"' -n tcp -s 88 -w 'core_UL.pcap'; sleep 0.00001'
    fi
fi

if "$DL"
  then
    echo "dst_port: $dst_port"
    echo "dst_addr: $dst_addr"
    echo "cc frequency: $frequency"
    echo "cc alg: $cc"
    echo "iperf duration: $iperf_duration"
    echo "Dumping cc data in $cc_file_name"
    echo "downlink"

    while true; do
      if ! (tmux has-session -t "${iperf_client_tmux_name}${cli_num}")
        then
	  tmux new-session -d -s "${cc_tmux_name}${cli_num}" './ss_script.sh '"$dst_addr"' '"$frequency"' > '"core_${cc}_${dst_addr}_${dst_port}_DL_${cli_num}"'; sleep 0.00001'	
          sleep 1s
	  tmux new-session -d -s "${iperf_client_tmux_name}${cli_num}" iperf3 -c "$dst_addr" -t "$iperf_duration" -C "$cc" -p "$dst_port"
          date +%H%M%S.%6N
          break
      fi
      let "cli_num=cli_num+1"
    done

    while tmux has-session -t "iperf_client"; do
      sleep 5s
    done
    tmux kill-server

else
  while true; do
      if ! (tmux has-session -t "${iperf_server_tmux_name}${srv_num}")
        then
          tmux new-session -d -s "${iperf_server_tmux_name}${srv_num}" iperf3 -s -p "$dst_port"
          break
      fi
      let "srv_num=srv_num+1"
  done

fi
