while true;
do
    ss -tin -H dst 10.2.141.16
    sleep $1;
done | ts '%.s;'
