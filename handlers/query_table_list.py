# -*- coding: UTF-8 -*-
# Date: 2018-12-29
# Author: tang
#
import json
from request_base_handler import BaseHandler
import tornado
from tornado.concurrent import run_on_executor
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
#     "model":"default",
#     "charset":"utf-8"
# }
#
class QueryTableListHandler(BaseHandler):

    def get(self):
        self.response_json(None, -1, 'Not implements')

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        logger.info("request remote client id is %s ..." % self.request.remote_ip)

        if self.request.body is None or len(self.request.body) == 0:
            self.response_json(None, -1, 'Invalid param!')

        logger.info("[Request]:%s" % self.request.body)

        try:
            params = json.loads(self.request.body)

            if not params.has_key('model'):
                if params.has_key('type') and params['type']=='mysql':
                    params['model']="default"
                elif params.has_key('type') and params['type']=='mssql':
                    params['model'] = "dbo"
                elif params.has_key('type') and params['type']=='oracle':
                    params['model'] = params['user']
                elif params.has_key('type') and params['type'] == 'postgresql':
                    params['model'] ="public"
                else:
                    pass

            ret=yield self.query_table_lists(**params)
            self.response_json(ret)
        except Exception as e:
            self.response_json(None, -1, 'error:%s' % str(e.args) )
        finally:
            pass

    @run_on_executor
    def query_table_lists(self, type, host, port, user, passwd, dbname, model, charset):
        if not isinstance(port, int):
            raise Exception('Invalid database port,should be integer')

        if not BaseHandler.dbmapper.has_key(type):
            raise Exception('Not Support databse type :%s' % type)

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
        lists = reader.get_table_lists(model)
        reader.close()
        return lists
