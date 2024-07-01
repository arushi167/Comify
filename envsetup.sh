#!/bin/bash

if [ -d "venv" ] 
then
    echo "Python virtual environment exists." 
else
    python3 -m virtualenv venv
fi

source venv/bin/activate

pip3 install -r requirements.txt


if [ -d "logs" ] 
then
    echo "Log folder exists." 
else
    mkdir logs
    touch logs/error.log logs/access.log
fi

sudo chmod -R 777 logs