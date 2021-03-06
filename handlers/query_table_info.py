# -*- coding: UTF-8 -*-
# Date: 2018-12-29
# Author: tang
#
import json
import tornado
from tornado.concurrent import run_on_executor
from request_base_handler import BaseHandler
import sys
import traceback
sys.path.append("..")
from logger_file import logger

# Request: post
# Params:
# {
#     "type":"oracle",
#     "host":"172.16.90.252",
#     "port":1521,
#     "user":"yi_bo",
#     "passwd":"yi_bo",
#     "dbname":"orcl",
#     "model":"sys",
#     "charset":"utf-8",
#     "src_table":"TEST_TABLE",
#     "dest_table":"my_test_table"
# }
#


class QueryTableInfoHandler(BaseHandler):

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
                    params['model'] = "default"
                elif params.has_key('type') and params['type']=='mssql':
                    params['model'] = "dbo"
                elif params.has_key('type') and params['type']=='oracle':
                    params['model'] = params['user']
                elif params.has_key('type') and params['type'] == 'postgresql':
                    params['model'] ="public"
                else:
                    pass

            ret = yield self.query_table_info(**params)
            self.response_json(ret)
        except Exception as e:
            self.response_json(None, -1, 'error:%s' % str(e.args) )
        finally:
            pass

    @run_on_executor
    def query_table_info(self, type, host, port, user, passwd, dbname, model,charset, src_table, dest_table):

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
        try:
            ret, create_table_sql, columns_names, key_columns_names = reader.get_mysql_create_table_sql(model, src_table,
                                                                                                    dest_table, True)
            lists = reader.get_table_lists(model)
        except Exception as e:
            logger.exception(e)
            raise e
        finally:
            reader.close()

        if ret is not True:
            raise Exception("failed,reason:%s" % create_table_sql)

        result = {}
        for item in lists:
            if item['table_name'] == src_table:
                result['metadata'] = item
                break

        result['create_sql'] = create_table_sql
        result['columns'] = columns_names
        result['primary_key'] = key_columns_names
        return result
