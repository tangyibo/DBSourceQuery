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


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
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

    app = Application()
    server = tornado.httpserver.HTTPServer(app)
    listen_port = 8088
    server.listen(listen_port)
    logger.info("start on port=%s ..." % listen_port)
    tornado.ioloop.IOLoop.instance().start()
