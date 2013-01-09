#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser

config = ConfigParser()
config.read("config.ini")

def qqcfg():
    qq = config.get('account', 'qq')
    pw = config.get('account', 'pw')
    return (qq, pw)

def botcfg():
    enable = config.get('bot', 'enable')
    store = config.get('bot', 'store')
    return (enable, store)
