BIN_NAME=dbSourceQuery
OUTPUT_DIR:= ./bin
SRC:= ./
VENV_BIN_DIR=venv/bin

all : build

run : clean
	${VENV_BIN_DIR}/python src/server.py 

clean :
	-rm -rf ${SRC}/*.pyc >>/dev/null
	-rm -rf ${SRC}/dbreader/*.pyc >>/dev/null
	-rm -rf ${SRC}/handlers/*.pyc >>/dev/null
	-rm -rf ${SRC}/eureka_client/*.pyc >>/dev/null
	-rm -rf ${SRC}/obj >>/dev/null
	-rm -rf ./*.spec >>/dev/null
	-rm -rf ${OUTPUT_DIR}/*  >>/dev/null

build : clean
	${VENV_BIN_DIR}/pyinstaller --clean  -F ${SRC}/*.py  --distpat ${OUTPUT_DIR} --workpath ${SRC}/obj --name ${BIN_NAME}
	\cp ${SRC}/config.ini ${OUTPUT_DIR}/
	\cp ${SRC}/logger.ini ${OUTPUT_DIR}/
	\cp ${SRC}/sbin/* ${OUTPUT_DIR}/
	chmod u+x ${OUTPUT_DIR}/*.sh
	unzip -d ${OUTPUT_DIR}/ ${SRC}/oracle/instantclient-basic-linux.x64-12.2.0.1.0.zip
	unzip -d ${OUTPUT_DIR}/ ${SRC}/oracle/instantclient-sdk-linux.x64-12.2.0.1.0.zip

.PHONY : clean run build



