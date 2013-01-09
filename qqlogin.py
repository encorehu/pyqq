#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: maplebeats
# gtalk/mail: maplebeats@gmail.com

#from urllib import parse,request
#from http import cookiejar
import random
import json,hashlib
import gzip
import os
from logger import logger

import urllib
import urllib2
import cookielib
import SimpleHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import StringIO

COOKIE="cookie.txt"
IMG="verify.png"

#from http.server import SimpleHTTPRequestHandler, HTTPServer

class VHTTPhandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        path = self.translate_path(IMG)
        try:
            f = open(path,"rb")
        except FileNotFoundError:
            self.send_error(404, "Not file find")
        self.send_response(200)
        self.send_header("Content-type", "image/png")
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()
        ViewVerify.stop()

class ViewVerify():

    @classmethod
    def start(cls):
        cls.httpd = HTTPServer(('',8000), VHTTPhandler)
        print("please open http://localhost:8000/%s"%(IMG)) #TODO
        try:
            cls.httpd.serve_forever()
        except ValueError:
            pass

    @classmethod
    def stop(cls):
        cls.httpd.server_close()

class QQlogin(object):

    def _hexchar2bin(self, num):
        arry = bytearray()
        for i in range(0, len(num), 2):
            arry.append(int(num[i:i+2],16))
        return arry

    def _preprocess(self, password=None, verifycode=None):
        self.__hashpasswd = self.md5(password) #store hashed password
        I = self._hexchar2bin(self.__hashpasswd)
        H = self.md5(I + bytearray(verifycode[2]))
        G = self.md5(H + verifycode[1].upper())
        return G

    def md5(self, s):
        try:
            s = s.encode('utf-8')
        finally:
            return hashlib.md5(s).hexdigest().upper()

    def _request(self, url, data=None, cookie=False):
        logger.debug("OUT:\n%s<--%s\n" %(url, data))
        if data:
            data = urllib.urlencode(data).encode('utf-8')
            rr = urllib2.Request(url, data, self._headers)
        else:
            rr = urllib2.Request(url=url, headers=self._headers)
        fp = self.opener.open(rr)
        if fp.info().get('Content-Encoding') == 'gzip':
            compresseddata = fp.read()
            compressedstream = StringIO.StringIO(compresseddata)
            gzipper = gzip.GzipFile(fileobj=compressedstream)
            f = gzipper.read() 
            #f = gzip.decompress(fp.read())
            res = f.decode('utf-8')
        else:
            try:
                res = fp.read().decode('utf-8')
            except:
                res = fp.read()
                logger.debug("IN-raw:\n%s"%res)
        if fp.info().get('Content-Type') == 'text/plain; charset=utf-8':
            res = json.loads(res)
            if res['retcode'] == 0: #success
                res = res['result']
            elif res['retcode'] == 103: #cookie was timeout
                os.remove(COOKIE)
            elif res['retcode'] == 102: #ok
                res = None
            elif res['retcode'] == 114: #send msg fail TODO:retry
                res = None
            elif res['retcode'] == 116: #update ptwebqq value
                res = tuple([res.update({"poll_type":"ptwebqq"})])
            else:
                logger.error(url)
                res = None
        if cookie:
            self.cookieJar.save(ignore_discard=True, ignore_expires=True)
        fp.close()
        logger.debug("IN:\n%s"%res)
        return res
    
    def __init__(self, qq, pw):
        self.qq = qq
        self._pw = pw
        self.appid = "2001601"
        self.cookieJar = cookielib.MozillaCookieJar(COOKIE)
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))
        self._headers = {
            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1",
            "Accept-Language":"zh-cn,en;q=0.8,en-us;q=0.5,zh-hk;q=0.3",
            "Accept-Encoding":"gzip;deflate",
            "Connection":"keep-alive",
            "Referer":"http://web.qq.com"
        }

    def _getverifycode(self):
        url = 'http://check.ptlogin2.qq.com/check?uin=%s&appid=%s&r=%s'%(self.qq, self.appid, random.Random().random())
        res = self._request(url = url)
        verify =  eval(res.split("(")[1].split(")")[0])
        verify = list(verify)
        if verify[0] == '1':
            img = "http://captcha.qq.com/getimage?aid=%s&r=%s&uin=%s"%(self.appid, random.Random().random(), self.qq)
            with open(IMG,"wb") as f:
                f.write(urllib2.urlopen(img).read())
            ViewVerify.start()
            verify[1] = input("验证码:").strip()
        return verify

    def test(self):
        """
        login webqq
        """
        self._verifycode = self._getverifycode()
        self.pswd = self._preprocess(self._pw, self._verifycode) 
        self._headers.update({"Referer":"http://ui.ptlogin2.qq.com/cgi-bin/login?target=self&style=5&mibao_css=m_webqq&appid=%s"%(self.appid)+"&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fweb.qq.com%2Floginproxy.html&f_url=loginerroralert&strong_login=1&login_state=10&t=20121029001"})
        url = "http://ptlogin2.qq.com/login?u=%s&p=%s&verifycode=%s&aid=%s"%(self.qq,self.pswd,self._verifycode[1],self.appid)\
        + "&u1=http%3A%2F%2Fweb.qq.com%2Floginproxy.html%3Flogin2qq%3D1%26webqq_type%3D10&h=1&ptredirect=0&ptlang=2052&from_ui=1&pttype=1&dumy=&fp=loginerroralert&action=3-25-30079&mibao_css=m_webqq&t=1&g=1"
        res = self._request(url=url)
        if res.find(u"登录成功") != -1:
            logger.info(u"登录成功")
        elif res.find(u"验证码不正确") != -1:
            logger.error(u"验证码错误")
            self._getverifycode()
            self.test()
        else:
            logger.error(res)

if __name__ == "__main__":
    from config import qqcfg
    c = qqcfg()
    q = QQlogin(c[0],c[1])
    q.test()
