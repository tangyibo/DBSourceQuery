#!/bin/bash

# export environment
export LD_LIBRARY_PATH=/usr/local/whistle/oracle/instantclient_12_2:$LD_LIBRARY_PATH  
export OCI_LIB_DIR=/usr/local/whistle/oracle/instantclient_12_2  
export OCI_INC_DIR=/usr/local/whistle/oracle/instantclient_12_2/sdk/include  
export NLS_LANG=AMERICAN_AMERICA.UTF8

DS_PROG="server.py"
DS_HOME=`pwd`

mkdir ${DS_HOME}/log >/dev/null 2>&1

#start server program
nohup /opt/DBSourceQuery/venv/bin/python2 ${DS_HOME}/${DS_PROG} >>log/runtime.log 2>&1 &
