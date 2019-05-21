#!/bin/bash

DS_PROG="dbSourceQuery"
DS_HOME=`pwd`

# export environment
export LD_LIBRARY_PATH=${DS_HOME}/instantclient_12_2:$LD_LIBRARY_PATH  
export OCI_LIB_DIR=${DS_HOME}/instantclient_12_2  
export OCI_INC_DIR=${DS_HOME}/instantclient_12_2/sdk/include  
export NLS_LANG=AMERICAN_AMERICA.UTF8


mkdir ${DS_HOME}/log >/dev/null 2>&1

#start server program
nohup ${DS_HOME}/${DS_PROG} >>log/runtime.log 2>&1 &
