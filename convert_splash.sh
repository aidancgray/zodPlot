#!/bin/bash

for filename in ~/src/zodPlot/splash_screen/*.bmp; do
    python ~/src/zodPlot/bmp_to_fb.py "$filename"
    rm -f "$filename"
done
