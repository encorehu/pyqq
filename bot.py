#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: maplebeats
# gtalk/mail: maplebeats@gmail.com

#from urllib import request,parse
#from http import cookiejar
import urllib
import urllib2
import cookielib
import json
from webqq import Webqq
import re
import threading
from logger import logger
#import sqlite3

class Bot:

    def _request(self, url, data=None, opener=None):
        if data:
            data = urllib.urlencode(data).encode('utf-8')
            rr = urllib2.Request(url, data, self._headers)
        else:
            rr = urllib2.Request(url=url, headers=self._headers)
        #with opener.open(rr) as fp:
        fp = opener.open(rr)
        try:
            res = fp.read().decode('utf-8')
        except:
            res = fp.read()
        return res

    def __init__(self):
        self.simi_init()
        self.link = re.compile(r'[a-z]')

    def gettitle(url):
        re = urllib2.urlopen(url).read(1024)
        pass

    def reply(self, req):
        if req.find('%') == -1:
            return self.simi_bot(req) or self.hito_bot()
        else:
            return self.hito_bot()

    def simi_init(self):
        simi_Jar = cookielib.CookieJar()
        self.simi_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(simi_Jar))
        self._headers = {
                         "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1",
                         "Accept-Language":"zh-cn,en;q=0.8,en-us;q=0.5,zh-hk;q=0.3",
                         "Accept-Encoding":"deflate",
                         "Referer":"http://www.simsimi.com/talk.htm?lc=ch"
        }
        url = "http://www.simsimi.com/func/req?%s" % urllib.urlencode({"msg": "hi", "lc": "ch"})
        self._request(url=url, opener=self.simi_opener)

    def simi_bot(self, req):
        """
        req could not have % ...
        """
        #logger.debug(repr(req))
        #logger.debug(urllib.urlencode({"msg": req.encode('utf-8'), "lc": "zh"}))
        url = "http://www.simsimi.com/func/req?%s" % urllib.urlencode({"msg": req.encode('utf-8'), "lc": "zh"})
        
        res = self._request(url, opener=self.simi_opener)
        if res == "{}":
            return False
        else:
            return json.loads(res)['response']

    def hito_bot(self):
        url = "http://api.hitokoto.us/rand"
        res = urllib2.urlopen(url).read().decode()
        hit = json.loads(res)
        return hit['hitokoto']

class BotHandler:
    def __init__(self,name,bot):
        self.name_ =name
        self.bot_ = bot
    def grouphandler(self,uin,cmd):
        self.bot_.send_group_msg(uin,cmd)
    #def name(self):

class EchoBotHandler(BotHandler):
    def __init__(self,bot):
        BotHandler.__init__(self,"echo",bot)
    def grouphandler(self,uin,cmd):
        self.bot_.send_group_msg(uin,cmd)
        
class Qbot(Webqq):

    def __init__(self, qq, ps):
        super(Qbot, self).__init__(qq, ps)
        self.bot = Bot()
        self.handles =[]
        b = EchoBotHandler(self)
        self.handles.append(b)
    
    def findHandler(self,name):
        debugstr = 'find:'+name+'\n'
        print(debugstr)
        for v in self.handles:
            debugstr = 'Handler:'+v.name_+'\n'
            print(debugstr)
            if v.name_ == name:
                return v
        return None

    def grouphandler(self, data):
        #logger.debug(data)
        #content_list = data['content'][1]
        content_list = data['content'] # a list contains cface text
        content = ''
        for piece in content_list:
            if type(piece) == list:
                continue
            else:
                content += piece
        content = content.strip()
        if len(content)==0: # cface without text
            pass
        else:
            #logger.debug(content)
            if(content[0] =='@'):
                re = u'命令行可以使用'
                cmdcontent=content[1:]
                cmds = cmdcontent.split(':',2)
                h=self.findHandler(cmds[0])
                if(h!=None):
                    h.grouphandler(data['from_uin'],cmds[1])
                else:
                    self.send_group_msg(data['from_uin'], u'你能说人话么, 我怎么听不懂')
                #re = u"命令："+cmds[0]+'内容：'+cmds[1]
                #self.send_group_msg(data['from_uin'], re)
            else:
                re = self.bot.reply(content)
                self.send_group_msg(data['from_uin'], re)
            logger.info("IN:%s\nreply group:%s"%(content, re))

    def userhandler(self, data):
        content = data['content'][1]
        re = self.bot.reply(content)
        self.send_user_msg(data['from_uin'], re)
        logger.info("IN:%s\nreply user:%s"%(content, re))

if __name__ == "__main__":
    from config import qqcfg
    c = qqcfg()
    qq = Qbot(c[0],c[1])
    qq.login()
