#!/bin/sh

echo "Launching Docker-gen"
/usr/local/bin/docker-gen -watch -notify "/usr/bin/python /home/run/ec2.py" routes.tmpl routes.txt
