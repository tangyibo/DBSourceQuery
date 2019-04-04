# -*- coding: UTF-8 -*-
# Date: 2018-12-29
# Author: tang
#
import tornado.web
import json
from concurrent.futures import ThreadPoolExecutor
from dbreader import *
import sys
sys.path.append("../")
from logger_file import logger

class BaseHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(20)

    dbmapper = {
        "mysql": ReaderMysql,
        "oracle": ReaderOracle,
        "mssql": ReaderSqlserver
    }

    def respose_html(self, data):
        raise Exception("Not Implement!")

    def response_json(self, data, errcode=0, errmsg='ok'):
        result = {
            "errcode": errcode,
            "errmsg": errmsg,
            "data": data if data is not None else ''
        }

        resp = json.dumps(result)
        logger.info("[Response]:%s" % resp)
        self.finish(result)

    def get(self):
        logger.info("[Request-GET]:%s" % self.request.uri)
        self.response_json(None, 404, 'Not found!')

    def post(self):
        logger.info("[Request-POST]:%s" % self.request.uri)
        self.response_json(None, 404, 'Not found!')
