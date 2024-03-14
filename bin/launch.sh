#!/usr/bin/env bash

srcDir=/home/idg/src/zodPlot
source $srcDir/venv/bin/activate

now=`date +"%Y-%m-%d_%H-%M-%S"`

nohup python $srcDir/load_splash.py $srcDir/splash_screen 0.05 >/dev/null 2>&1 &

nohup python $srcDir/wait_for_start.py >/dev/null 2>&1
startCode=$?

if (( $startCode == 1 ))
then
    printf "SECRET START!\n"
    cp $srcDir/screens/blank.fb /dev/fb0

elif (( $startCode == 2 ))
then
    printf "SECRET ~OTHER~ START!\n"
    cp $srcDir/screens/blank.fb /dev/fb0
else
    if mountpoint -q /mnt/usbLog
    then
        printf "USB Drive mounted\nStarting ZODPlot processes\n"
        nohup python $srcDir/main.py \
            --logLevel=20 \
            --updateTime=34 \
            --gain=10000 \
            --imgLog=/mnt/usbLog/ \
            "$@" >& /mnt/usbLog/$now.log &
    
    else
        printf "USB Drive NOT mounted\nStarting ZODPlot processes\n"
        nohup python $srcDir/main.py \
            --logLevel=20 \
            --updateTime=34 \
            --gain=10000 \
            >/dev/null 2>&1 &
    fi
fi