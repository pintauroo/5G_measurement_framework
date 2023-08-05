#!/bin/bash

base_path="./"
data_folder="Data/"
wireless_folder="Data/WirelessData/"

# folder_name="1UE_1018_cubic_first_100sec_DL_24prb" 
# folder_name="1UE_1018_cubic_first_100sec_UL_24prb"
# folder_name="1UE_1018_reno_first_100sec_DL_24prb"
# folder_name="1UE_1018_reno_first_100sec_UL_24prb"
# folder_name="1UE_1018_vegas_first_100sec_DL_24prb"
# folder_name="1UE_1018_vegas_first_100sec_UL_24prb"
# folder_name="1UE_1018_westwood_first_100sec_UL_24prb"
# folder_name="1UE_1018_yeah_first_100sec_DL_24prb"
# folder_name="1UE_1018_yeah_first_100sec_UL_24prb"

folder_name="1UE_1018_cubic_first_100sec_DL_106prb"
# folder_name="1UE_1018_cubic_first_100sec_UL_106prb"
# folder_name="1UE_1018_reno_first_100sec_DL_106prb"
# folder_name="1UE_1018_reno_first_100sec_UL_106prb"

# folder_name="1033_first100sec_cubic_reno_1ue_2streams_24prb_DL"
# folder_name="1033_first100sec_cubic_reno_1ue_2streams_24prb_UL"

path=$base_path$data_folder$folder_name
wireless_path=$base_path$wireless_folder$folder_name
reps=()

echo "$path"
echo "$wireless_path"
extension='.pcap'
# find $folder_name -type f -name "*.pcap"



############################
# extract zip files
############################
files=($(find "$path" -type f))
for file in "${files[@]}"; do
    if [[ $file =~ 'tar.gz' ]]; then
        echo "Extracting $file"
        tar -xzf $file -C $path
    fi
done


files=($(find $path -type f -name "*$extension" -exec basename {} \;))
# files=($(find $path -type f -name "*v1*" -exec basename {} \;))

for file in "${files[@]}"; do
  suffix="${file##*_}"
  run="${suffix%.*}"
    # echo $file
    # IFS="_" read -r ue cc ip port run <<< "$file"
    # run=${run%.pcap}
    # echo $ue
    # echo $cc
    # echo $ip
    # echo $port
  if [[ ! " ${reps[*]} " == *" $run "* ]]; then
    reps="$reps $run"
  fi
done

files=($(find "$path" -type f))
files_wireless=($(find "$wireless_path" -type f))
echo $files_wireless

for rep in $reps; do

    ues=()
    core=''
    ccs=()
    echo
    echo "Processing run: $rep"

    for file in "${files[@]}"; do
      if [[ $file =~ $rep ]]; then

        extension="${file##*.}"

        if [[ ! $file =~ "merged" && ! $file =~ '.pdf' && ! $file =~ '.zip' ]]; then

          
          if [[ $file =~ "ue"  &&  $file =~ "$rep.pcap" ]]; then
            ues+=($file)
          elif [[ $file =~ "core"  &&  $file =~ "$rep.pcap" ]]; then
            core=$file
          elif [[ $file =~ "$rep.cc" ]]; then
            ccs+=($file)
          fi

        fi
      fi
    done

    for file in "${files_wireless[@]}"; do
      if [[ "$file" == *"${rep}.csv" ]]; then
        wireless=$file
      fi
    done

    echo 'Found files:'

    # UE
    for value in "${ues[@]}"; do
        echo "$value"
    done
    # CC
    for value in "${ccs[@]}"; do
        echo "$value"
    done
    # CORE
    echo $core

    # WIRELESS
    echo $wireless

    cd $path

    if [[ $folder_name =~ 'UL' ]]; then
      echo "UpLink!"
      if [[ $folder_name =~ '106prb' ]]; then
        echo "106prb"
        python $base_path'pcap_parser_single_flow_broken_FIN.py' "${ues[@]}" $core $ccs $wireless $folder_name$rep > "pcap_processing$rep.out" 2>&1 #UL
      elif [[ $folder_name =~ '24prb' ]]; then
        echo "24prb"
        python $base_path'pcap_parser.py' "${ues[@]}" $core $ccs $wireless $folder_name$rep > "pcap_processing$rep.out" 2>&1 #UL
      fi
    else
      echo "DownLink!"
      if [[ $folder_name =~ '106prb' ]]; then
        echo "106prb"
        python $base_path'pcap_parser_single_flow_broken_FIN.py'  $core "${ues[@]}" $ccs $wireless $folder_name$rep > "pcap_processing$rep.out" 2>&1 #DL
      elif [[ $folder_name =~ '24prb' ]]; then
        echo "24prb"
        python $base_path'pcap_parser.py'  $core "${ues[@]}" $ccs $wireless $folder_name$rep > "pcap_processing$rep.out" 2>&1 #DL
      fi
    fi

    mv wireless_data.csv csv_data
    # move csvdata
    if [ -d "csv_data" ]; then
      if [ -d csv_data$rep ]; then
        rm -rf csv_data$rep
        mv -fT csv_data csv_data$rep
      else
          mv -fT csv_data csv_data$rep
      fi
    else
      echo "Error building csv files!"
    fi
    
    # move pdf
    if [ -f "$base_path/plot_complete$folder_name$rep.pdf" ]; then
      mv -fT $base_path/plot_complete$folder_name$rep.pdf plot_complete$folder_name$rep.pdf
    else
      echo "Error building plots!"
    fi
done