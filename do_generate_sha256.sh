echo Generating sha256 values every 5 seconds, use CTRL-C to stop
cd scripts
while true
do
    ./generate_sha256.sh
    sleep 5
done
