#!/usr/bin/env bash

printf "killing ZODPLOT services...\n"
for pid in $(pgrep -f 'main.*.py'); do sudo kill $pid; done
printf "done\n"