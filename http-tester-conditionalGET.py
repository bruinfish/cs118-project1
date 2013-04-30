#!/usr/local/cs/bin/python

from threading import Thread
from httplib import HTTPConnection
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from datetime import datetime, timedelta
from bcolor import bcolors
import sys
import time
import re, socket, calendar


class TestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/basic":
            lms = self.headers.get('If-Modified-Since', "")
            cdata = ""
            if lms != "":
                m_ts = calendar.timegm(time.strptime(lms, "%a, %d %b %Y %H:%M:%S GMT"))
                c_ts = calendar.timegm(time.gmtime())
                if c_ts - m_ts > 5:
                    lastModify=lms
                    expireDate=(datetime.utcnow()+timedelta(seconds=5)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                    self.send_response(304)
                    self.send_header('Expire',expireDate)
                    self.send_header('Last-Modified', lastModify)
                else:
                    cdata = "WRONG!\n"
                    size = len(cdata)
                    expireDate=(datetime.utcnow()+timedelta(seconds=5)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                    lastModify=(datetime.utcnow()).strftime("%a, %d %b %Y %H:%M:%S GMT")
                    self.send_response(200)
                    self.send_header('Content-type','text/html')
                    self.send_header('Content-length', str(size))
                    self.send_header('Expire',expireDate)
                    self.send_header('Last-Modified', lastModify)

            else:
                cdata = open("./basic", "r").read()
                size = len(cdata)
                expireDate=(datetime.utcnow()+timedelta(seconds=5)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                lastModify=(datetime.utcnow()).strftime("%a, %d %b %Y %H:%M:%S GMT")
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.send_header('Content-length', str(size))
                self.send_header('Expire',expireDate)
                self.send_header('Last-Modified', lastModify)

            if self.close_connection == True:
                self.send_header('Connection', 'close')
            self.end_headers()
            if cdata != "":
                print "Send data"
                self.wfile.write(cdata)

        return


class ServerThread (Thread):
    def __init__(self, port):
        Thread.__init__(self)
        self.port = port

    def run(self):
        try:
            TestHandler.protocol_version = "HTTP/1.1"
            self.server = HTTPServer(('', self.port), TestHandler)
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.server.socket.close() 


try:
    conf = open("./portconf", "r")
    pport  = conf.readline().rstrip().split(':')[1]
    sport1 = conf.readline().rstrip().split(':')[1]
    sport2 = conf.readline().rstrip().split(':')[1]
    server1 = ServerThread(int(sport1))
    server1.start()
    dataFile = open('basic', "r")
    cdata = dataFile.read()
    r = False
    proxy = '127.0.0.1:'+pport
    conn = HTTPConnection(proxy)
    conn.request("GET", "http://127.0.0.1:19900/basic")
    resp = conn.getresponse()
    lms = resp.getheader('last-modified', "")
    data = resp.read()
    conn.close()

    print "1 " + data

    time.sleep(3)
    conn2 = HTTPConnection(proxy)
    hdrs = {"If-Modified-Since": lms}
    conn2.request("GET", "http://127.0.0.1:19900/basic", headers=hdrs)
    resp2 = conn2.getresponse()
    data2 = resp2.read()
    conn2.close()

    print "2 " + data2

    time.sleep(3)
    conn3 = HTTPConnection(proxy)
    conn3.request("GET", "http://127.0.0.1:19900/basic", headers=hdrs)
    resp3 = conn3.getresponse()
    data3 = resp3.read()
    conn3.close()

    print "3 " + data3
    print resp3.status

    if int(resp3.status) == 304 and data2 == cdata:
        r = True
    if r:
        print "Re-query Caching: [" + bcolors.PASS + "PASSED" + bcolors.ENDC + "]"
    else:
        print "Re-query Caching: [" + bcolors.FAIL + "FAILED" + bcolors.ENDC + "]"
except:
    server1.server.shutdown()

server1.server.shutdown()

