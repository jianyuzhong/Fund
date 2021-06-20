"""The logger object."""

# -*- coding:utf-8 -*-

import logging
import os
import threading
import time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .mslogconfig import (MsConsoleLogConfig, MsFileLogConfig, MsLogConfig,
                          MsLogMessageConfig)
from .msloglevel import MsLogLevel, MsLogLevels


class MsLogger(object):
    """The logger object."""
    def __init__(
        self,
        name: str,
        lvl: MsLogLevel = MsLogLevels.DEBUG,
        msmsgcfg: MsLogMessageConfig = None,
        mscslogcfg: MsConsoleLogConfig = None,
        msficfg: MsFileLogConfig = None,
    ):
        self.name = name
        self.level = lvl
        self._msmsgcfg = msmsgcfg
        self._mscslogcfg = mscslogcfg
        self._msficfg = msficfg

        # ERROR = MsLogLevel(4, "Error")
        # WARN = MsLogLevel(3, "Warn")
        # CRITICAL = MsLogLevel(5, "Critical")
        # INFO = MsLogLevel(2, "Info")
        # DEBUG = MsLogLevel(1, "Debug")
        # TRACE = MsLogLevel(0, "Trace")
        # NOTSET = MsLogLevel(0, "NotSet")

        # CRITICAL: int
        # FATAL: int
        # ERROR: int
        # WARNING: int
        # WARN: int
        # INFO: int
        # DEBUG: int
        # NOTSET: int
        self._pylvl: int = self._get_logging_level(self.level)

        self._innerlogger: logging.Logger = self.__create_innerlogger(
            self.name)

    def __create_innerlogger(self, name: str = None):
        # logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # file handler
        if not os.path.isdir(self._msficfg.log_file_dir):
            os.makedirs(self._msficfg.log_file_dir)
        logfile = os.path.join(self._msficfg.log_file_dir,
                               self._msficfg.log_file_name)
        fh = RotatingFileHandler(logfile,
                                 mode='w',
                                 maxBytes=self._msficfg.log_file_maxsize,
                                 backupCount=self._msficfg.log_file_maxcount,
                                 encoding=self._msficfg.log_file_enc.name)
        fh.setLevel(self._pylvl)
        logger.addHandler(fh)

        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(self._pylvl)
        #ch.setFormatter(formatter)
        logger.addHandler(ch)

        # new_msg = '[%s] [%s] [%d] [%s] %s' % (time_stamp, lvl.name, tid, loggername, msg)
        formatter = logging.Formatter(
            # "[%(asctime)s] [%(levelname)s] [%(filename)s] [line:%(lineno)d]: %(message)s"
            "[%(asctime)s] [%(levelname)s] %(message)s")
        for hdlr in logger.handlers:
            hdlr.setFormatter(formatter)
        # fh.setFormatter(formatter)

        return logger

    def trace(self, msg: str):
        """Do log writing on MsLogLevel.Trace"""
        # self.log(msg, MsLogLevels.TRACE)

        self.log(msg, MsLogLevels.TRACE, threading.current_thread().ident)
        # self._innerlogger.log(
        #     logging.DEBUG,
        #     f'[{threading.current_thread().ident}] {msg}',
        # )

    def debug(self, msg: str):
        """Do log writing on MsLogLevel.Debug"""
        self.log(msg, MsLogLevels.DEBUG, threading.current_thread().ident)
        # self.log(msg, MsLogLevels.DEBUG)
        # self._innerlogger.log(
        #     logging.DEBUG,
        #     f'[{threading.current_thread().ident}] {msg}',
        # )

    def info(self, msg: str):
        """Do log writing on MsLogLevel.Info"""
        self.log(msg, MsLogLevels.INFO, threading.current_thread().ident)
        # self.log(msg, MsLogLevels.INFO)
        # self._innerlogger.log(
        #     logging.INFO,
        #     f'[{threading.current_thread().ident}] {msg}',
        # )

    def warn(self, msg: str):
        """Do log writing on MsLogLevel.Warn"""
        self.log(msg, MsLogLevels.WARN, threading.current_thread().ident)
        # self.log(msg, MsLogLevels.WARN)
        # self._innerlogger.log(
        #     logging.WARN,
        #     f'[{threading.current_thread().ident}] {msg}',
        # )

    def error(self, msg: str):
        """Do log writing on MsLogLevel.Error"""
        self.log(msg, MsLogLevels.ERROR, threading.current_thread().ident)
        # self.log(msg, MsLogLevels.ERROR)
        # self._innerlogger.log(
        #     logging.ERROR,
        #     f'[{threading.current_thread().ident}] {msg}',
        # )

    def critical(self, msg: str):
        """Do log writing on MsLogLevel.Critical"""
        self.log(msg, MsLogLevels.CRITICAL, threading.current_thread().ident)
        # self.log(msg, MsLogLevels.CRITICAL)
        # self._innerlogger.log(
        #     logging.CRITICAL,
        #     f'[{threading.current_thread().ident}] {msg}',
        # )

    def log(self,
            msg: str,
            msloglvl: MsLogLevel = MsLogLevels.DEBUG,
            eventid: int = -1,
            formatter=None):
        """"""

        if msloglvl == MsLogLevels.NOTSET:
            return

        lvl = self._get_logging_level(msloglvl)
        # if msloglvl == MsLogLevels.TRACE or msloglvl == MsLogLevels.DEBUG:
        #     # self.debug(msg)
        #     lvl = logging.DEBUG
        # elif msloglvl == MsLogLevels.INFO:
        #     # self.info(msg)
        #     lvl = logging.INFO
        # elif msloglvl == MsLogLevels.WARN:
        #     # self.warn(msg)
        #     lvl = logging.WARN
        # elif msloglvl == MsLogLevels.ERROR:
        #     # self.error(msg)
        #     lvl = logging.ERROR
        # elif msloglvl == MsLogLevels.CRITICAL:
        #     # self.critical(msg)
        #     lvl = logging.CRITICAL

        self._innerlogger.log(
            lvl,
            f'[{threading.current_thread().ident}] [{self.name}]: {msg}',
        )

    @classmethod
    def _get_logging_level(cls, msloglvl: MsLogLevel) -> int:
        _pylvl = logging.DEBUG
        if msloglvl == MsLogLevels.NOTSET:
            _pylvl = logging.NOTSET
        elif msloglvl == MsLogLevels.TRACE or msloglvl == MsLogLevels.DEBUG:
            _pylvl = logging.DEBUG
        elif msloglvl == MsLogLevels.INFO:
            _pylvl = logging.INFO
        elif msloglvl == MsLogLevels.WARN:
            _pylvl = logging.WARN
        elif msloglvl == MsLogLevels.ERROR:
            _pylvl = logging.ERROR
        elif msloglvl == MsLogLevels.CRITICAL:
            _pylvl = logging.CRITICAL

        return _pylvl
