#!/usr/bin/python
# -*- coding: UTF-8 -*-
# Date: 2018-12-29
# Author: tang
#
import sys
from logger_file import *
from handlers import *
import tornado.ioloop
import tornado.web
import tornado.httpserver
import config
import eureka_client.eureka_client as eureka_client


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/query_model_list', QueryModelListHandler),
            (r'/query_table_list', QueryTableListHandler),
            (r'/query_table_info', QueryTableInfoHandler),
            (r'.*', BaseHandler)
        ]
        settings = dict(
            debug=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # register your server to eureka server and also start to send heartbeat every 30 seconds
    eureka_client.init_registry_client(eureka_server=config.eureka_server,
                                       app_name=config.app_name,
                                       instance_port=config.listen_port,
                                       home_page_url="",
                                       status_page_url="",
                                       health_check_url="")
    app = Application()
    server = tornado.httpserver.HTTPServer(app)

    server.listen(config.listen_port)
    logger.info("start on port=%s ..." % config.listen_port)
    tornado.ioloop.IOLoop.instance().start()
