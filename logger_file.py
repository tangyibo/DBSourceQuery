# -*- coding: UTF-8 -*-

import logging
import logging.config

__all__ = ["logger"]


logging.config.fileConfig("./logger.ini")
logger = logging.getLogger("example01")
