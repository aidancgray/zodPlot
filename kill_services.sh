#!/usr/bin/env bash

printf "killing VIM-BCAST/PARLL services...\n"
for pid in $(pgrep -f 'main_.*.py'); do kill $pid; done
printf "done\n"