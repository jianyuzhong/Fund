"""
Ms log manager
"""

# -*- coding:utf-8 -*-

import logging
import os
import threading
import time

from .mslogconfig import (MsConsoleLogConfig, MsFileLogConfig, MsLogConfig,
                          MsLogMessageConfig)
from .mslogger import MsLogger
from .msloglevel import MsLogLevel, MsLogLevels


class MsLogManager(object):
    """the py logging"""

    _static_initialed: bool = False
    _static_initialed_locker = threading.RLock()

    def __init__(self):
        pass

    @classmethod
    def static_initial(cls,
                       dft_lvl: MsLogLevel = MsLogLevels.DEBUG,
                       msmsgcfg: MsLogMessageConfig = None,
                       msficfg: MsFileLogConfig = None,
                       mscslogcfg: MsConsoleLogConfig = None):
        """To initial the settings.
        dft_lvl: specifieds the default level of a MsLogger.
        msmsgcfg: specifieds the config for the MsLogMessege(the formatter, etc.).
        msficfg: specifieds the config for how to write a log file(the file logger level, etc.).
        mscslogcfg: specifieds the config for how to write log on console(the console logger level, etc.)."""

        if cls._static_initialed:
            return

        with cls._static_initialed_locker:
            if cls._static_initialed:
                return

            cls._dft_lvl = dft_lvl
            cls._msmsgcfg = msmsgcfg
            if cls._msmsgcfg is None:
                cls._msmsgcfg = MsLogMessageConfig()
            cls._msficfg = msficfg
            if cls._msficfg is None:
                cls._msficfg = MsFileLogConfig()
            cls._mscslogcfg = mscslogcfg
            if cls._mscslogcfg is None:
                cls._mscslogcfg = MsConsoleLogConfig()

            cls._pylvl: int = MsLogger._get_logging_level(cls._dft_lvl)
            logging.basicConfig(level=cls._pylvl)

            cls._loggers: dict = {}
            cls._loggers_locker = threading.RLock()

            cls._static_initialed = True

            # remove the default console handler in root logger
            rootlogger = logging.getLogger()
            rootlogger.handlers.clear()

    @classmethod
    def get_logger(cls,
                   name: str = None,
                   lvl: MsLogLevel = MsLogLevels.DEBUG) -> MsLogger:
        """Get (or create if not exits) a logger with specific logger name,
        or if 'name' is None, will return a logger with name 'default'"""

        if not cls._static_initialed:
            cls.static_initial()

        if cls._loggers.__contains__(name):
            return cls._loggers[name]

        with cls._loggers_locker:
            if cls._loggers.__contains__(name):
                return cls._loggers[name]

            logger: MsLogger = MsLogger(name, lvl, cls._msmsgcfg,
                                        cls._mscslogcfg, cls._msficfg)
            cls._loggers[name] = logger
        return logger