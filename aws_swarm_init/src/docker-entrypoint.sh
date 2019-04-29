#!/bin/sh

echo "Starting swarm manager ..."
echo $ENV $ROLE 
/usr/bin/python /home/run/swarm_init.py
