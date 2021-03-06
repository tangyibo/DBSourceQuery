# -*- coding: UTF-8 -*-
import ConfigParser

configFile = ConfigParser.ConfigParser()
configFile.read("./config.ini")

listen_port=configFile.getint("server", "listen_port")
app_name=configFile.get("server", "app_name")
eureka_enable=True if 1==int(configFile.get("server", "eureka_enable")) else False
eureka_server=configFile.get("server", "eureka_server")
svn_version=configFile.get("server", "svn_version")
