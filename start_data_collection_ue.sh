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

if ! (tmux has-session -t "iperf_capture")
  then
    if "$DL"
      then
        tmux new-session -d -s "iperf_capture" 'tcpdump -i '"$interface"' -n tcp -s 88 -w 'ue_DL.pcap'; sleep 0.00001' 
        echo "Dumping iperf session data in ue_DL.pcap"
    else
      tmux new-session -d -s "iperf_capture" 'tcpdump -i '"$interface"' -n tcp -s 88 -w 'ue_UL.pcap'; sleep 0.00001'
      echo "Dumping iperf session data in ue_UL.pcap"
    fi
fi

if "$DL"
  then
    while true; do
      if ! (tmux has-session -t "iperf_server${srv_num}")
        then
          tmux new-session -d -s "iperf_server${srv_num}" iperf3 -s -p "$dst_port"
          break
      fi
      let "srv_num=srv_num+1"
    done

else

  echo "dst_port: $dst_port"
  echo "dst_addr: $dst_addr"
  echo "cc frequency: $frequency"
  echo "cc alg: $cc"
  echo "iperf duration: $iperf_duration"
  echo "Dumping cc data in $cc_file_name"
  echo "uplink"

  while true; do
    if ! (tmux has-session -t "iperf_client${cli_num}")
      then
        tmux new-session -d -s "cc${cli_num}" './ss_script.sh '"$dst_addr"' '"$frequency"' > '"ue_${cc}_${dst_addr}_${dst_port}_UL_${cli_num}"'; sleep 0.00001'
        sleep 1s
        tmux new-session -d -s "iperf_client${cli_num}" iperf3 -c "$dst_addr" -t "$iperf_duration" -C "$cc" -p "$dst_port"
        date +%H%M%S.%6N
        break
    fi
    let "cli_num=cli_num+1"
  done

  while tmux has-session -t "iperf_client${cli_num}"; do
    sleep 5s
  done
  tmux kill-session -t "cc${cli_num}"

fi
