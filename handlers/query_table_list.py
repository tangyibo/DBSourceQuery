# -*- coding: UTF-8 -*-
# Date: 2018-12-29
# Author: tang
#
import json
from request_base_handler import BaseHandler
import sys
sys.path.append("..")
from logger_file import logger

# Request: post
# Params:
# {
#     "type":"mysql",
#     "host":"172.16.90.210",
#     "port":3306,
#     "user":"tangyibo",
#     "passwd":"tangyibo",
#     "dbname":"school_data",
#     "charset":"utf-8"
# }
#
class QueryTableListHandler(BaseHandler):

    def get(self):
        self.response_json(None, -1, 'Not implements')

    def post(self):
        logger.info("request remote client id is %s ..." % self.request.remote_ip)

        if self.request.body is None or len(self.request.body) == 0:
            self.response_json(None, -1, 'Invalid param!')

        logger.info("[Request]:%s" % self.request.body)

        try:
            params = json.loads(self.request.body)
            self.query_table_lists(**params)
        except Exception, e:
            self.response_json(None, -1, 'error:%s' % e.message)
        finally:
            pass

    def query_table_lists(self, type, host, port, user, passwd, dbname, charset):

        if not BaseHandler.dbmapper.has_key(type):
            self.response_json(None, -1, 'Not Support databse type :%s' % type)

        dbclass = BaseHandler.dbmapper.get(type)
        reader = dbclass(
            host=host,
            port=port,
            dbname=dbname,
            username=user,
            password=passwd,
            charset=charset
        )
        reader.connect()
        lists = reader.get_table_lists()
        reader.close()
        self.response_json(lists)
