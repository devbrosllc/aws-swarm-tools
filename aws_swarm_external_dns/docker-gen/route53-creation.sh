#!/bin/sh

echo "Starting ..."

file="entries"
lines=`cat $file`
for line in $lines; do
        echo "saving $line" >> output.txt
        # Perform other actions here
        
done