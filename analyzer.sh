#!/bin/bash

base_path="/home/andrea/Documents/Projects/dataset/"
folder_name="Dataset/new_oai_exp1_106prb_2UE_DL/new_oai_DL1_106prb"
path=$base_path$folder_name


reps=()

echo "$path"

extension='.pcap'
# find $folder_name -type f -name "*.pcap"


files=($(find $path -type f -name "*$extension" -exec basename {} \;))
# files=($(find $path -type f -name "*v1*" -exec basename {} \;))

for file in "${files[@]}"; do

    IFS="_" read -r ue cc ip port run <<< "$file"
    run=${run%.pcap}
    if [[ ! " ${reps[*]} " == *" $run "* ]]; then
      reps="$reps $run"
    fi
done


echo "$reps"


files=($(find "$path" -type f))


for rep in $reps; do
    ues=()
    core=''
    ccs=()
    echo
    echo "Processing run: $rep"

    for file in "${files[@]}"; do
      if [[ $file =~ $rep ]]; then
        # echo $file
        if [[ $file =~ "ue"  &&  $file =~ $extension ]]; then
          ues+=($file)

        elif [[ $file =~ "core" ]]; then
          core=$file
        elif [[ $file =~ "merged"  || $file =~ "pdf" ]]; then
          :
        else
          ccs+=($file)

        fi
      fi
    done

    for value in "${ues[@]}"; do
        echo "$value"
    done
    
    for value in "${ccs[@]}"; do
        echo "$value"
    done
    
    echo $core
    cd $path
    mergecap -F pcap -w merged$rep.pcap "${ues[@]}"
    python '/home/andrea/Documents/Projects/dataset/measurement-framework-master/colo_single_pcap.py' $core merged$rep.pcap $ccs $rep



done


