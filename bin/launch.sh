#!/bin/bash

srcDir=/home/idg/src/zodPlot
source $srcDir/venv/bin/activate

now=`date +"%Y-%m-%dT%H.%M.%S"`

nohup python $srcDir/load_splash.py $srcDir/splash_screen 0.05

if mountpoint -q /mnt/usbLog
then
    printf "USB Drive mounted\n"
    echo "USB Drive mounted\n" >> /mnt/usbLog/$now.log
    # nohup python $srcDir/main.py --logLevel=20 --updateTime=34 --gain=10000 "$@" >& /mnt/usbLog/$now.log &
else
    printf "USB Drive NOT mounted\n"
    # nohup python $srcDir/main.py --logLevel=20 --updateTime=34 --gain=10000 >/dev/null 2>&1 &
fi

