#!/bin/bash

srcDir=/home/idg/src/zodPlot
source $srcDir/venv/bin/activate

now=`date +"%Y-%m-%dT%H.%M.%S"`

python $srcDir/load_splash.py $srcDir/splash_screen 0.05