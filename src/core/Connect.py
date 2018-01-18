#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2018 <boutin_arnaud@hotmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os, re,  subprocess, platform, netifaces, json
import threading, time
from urllib import request
from io import StringIO
import sys
import signal
from core.PlayerTTS import PlayerTTS, Player
from core.PlayerMusic import PlayerMusic
from core.StreamCamera import StreamCamera

import socket
import  hashlib
#from streamClient import  PipelineClient
from core.StreamVocal import  StreamVocal
from core import PORT_CONTROL_SAT_CONNECT, PORT_HTTP, PORT_UPDATE_FILE,\
    PORT_MIN_SCAN, PORT_MAX_SCAN, PATH_RESOURCES, PATH_VOCAL, ACOUSTIC
import websocket

OSDETECT = platform.system()

def fermer_programme(signal, frame):
    print ("Fin programme...")
    sys.exit(0)
    
signal.signal(signal.SIGINT, fermer_programme)


class controlConnected(threading.Thread):
    
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
    
    def run(self):

        while 1:
            try :
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.s.bind(('', PORT_CONTROL_SAT_CONNECT))
                self.s.listen(5)
#                print 'controlConnected : En attente du client....'
                self.s.accept()
#                print 'controlConnected :  Connected by', address
            except Exception as e  :
                print ("controlConnected error : " + e.__str__())
                #[Errno 98] Address already in use
                if "[Errno 98]" in  e.__str__():
                    time.sleep(10)

class WSThread(threading.Thread):
        
    resources  = None
    isVocal = False 
         
    def __init__(self, parent):
        super(WSThread, self).__init__()
        self.parent = parent
 
        #current_dir = os.path.dirname(__file__)
        #script = 'resources.json'
        file_res = os.path.join(PATH_RESOURCES, 'resources.json')
        with open(file_res) as data_file:    
            self.resources = json.load(data_file)

        self.isVocal = True if self.resources["vocal"] == "True" else False


    def close(self):
        if hasattr(self, 'sc'):
            self.sc.stop()    
            del self.sc
                    
    def run(self):
        try:
            print ('Start socket thread')
            if self.parent.vocalActive and self.isVocal : 
                #self.sc = PipelineClient(self.parent)
                self.sc = StreamVocal(self.parent)
                self.sc.start()

            self.streamCamera = StreamCamera(self.parent.ipDetect)
            self.streamCamera.start()

                
            host = "ws://" + self.parent.ipDetect + ":" + str(PORT_HTTP)+ "/ws?service=monitoringVocalService"
            self.ws = websocket.WebSocketApp(host,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
            print ('Connect Thread : Socket ouverte')
            self.ws.run_forever()
            print ('Stop socket thread')
        except Exception as e:
            print ("erreur Connect : " + e.__str__())        
        finally:
            if hasattr(self, 'ws') :
                self.ws.close()
            self.close()

    def on_message(self, ws, message):
        try:
            response = json.load(StringIO(message.decode('utf-8')))
            print ("Retour serveur : " + response)
            if response == 'prete' and not hasattr(self, "sc") and self.isVocal:
                time.sleep(2)
                #self.sc = PipelineClient(self.parent)
                self.sc = StreamVocal(self.parent)
                self.sc.start()
            if response == 'Stop Vocal' and hasattr(self, "sc"):
                self.close()

        except Exception as e:
            print ("erreur Connect on_message : " + e.__str__())        



    def on_error(self, ws, error):
        print(error)
    
    def on_close(self, ws):
        self.close()
        print("### closed ###")

class Connexion():

    def __init__(self):
        print ("je rentre dans le programme")
        self.playertts = PlayerTTS()
        self.t_player = Player(self.playertts)
        self.t_player.start()
        self.playerMusic = PlayerMusic()
        self.playerMusic.start()

        self.c = controlConnected(self)
        self.c.start()
        
        if not os.path.exists(PATH_VOCAL):
            os.makedirs(PATH_VOCAL)

        directory_tmp = os.path.join(PATH_VOCAL, ACOUSTIC)
        if not os.path.exists(directory_tmp):
            os.makedirs(directory_tmp)
            
        self.ping = Ping()
        self.cn = CheckNetwork() 
        if not hasattr(self, 'WSthread'):
            self.WSthread = WSThread(self)
        

    def close(self):        
        self.WSthread.close()    
        
    def scan(self):
        try:
            while 1 :
                if not self.WSthread.isAlive() :
                    try:
                        self.detectIp()
                    except Exception as e:
                        print (os.path.dirname(os.path.realpath(__file__)))
                        print ("erreur : " + e.__str__())
                    if self.ipDetect :
                        self.WSthread = WSThread(self)
                        self.WSthread.start()

                time.sleep(10)
        except Exception as e:
            print ("erreur générale : " + e.__str__())
        

    def detectIp(self):
        self.ipDetect = None
        
        self.obj = dict()
        current_dir = os.path.dirname(__file__)
        #script = './resources/resources.json'
        #file_res = os.path.join(current_dir, script)
        file_res = os.path.join(PATH_RESOURCES, 'resources.json')
        with open(file_res) as data_file:    
            resources = json.load(data_file)
        
        header = {'Content-Type': 'application/json', 'User-Agent': 'python-micro'}
        while not self.ipDetect :
            (ip, macAddr) = self.cn.check_network()
            pingScan = self.ping.ping(ip)
            if self.ipDetect :
                pingScan.insert(0, self.ipDetect)
                
            self.obj['ip'] = ip
            self.obj['macAddr'] = macAddr
            self.obj['resources'] = resources
            jsonObj = json.dumps(self.obj, default=lambda o: o.__dict__)
            
            for ipDetect in pingScan :
                url = "http://" + ipDetect + ":"+str(PORT_HTTP)+"/ping"
                try:
                    req = request.Request(url, jsonObj.encode("utf-8"), header)
                    response = request.urlopen(req, timeout = 5)
                    resp = json.loads(response.read())

                    self.ipDetect = ipDetect
                    self.vocalActive = resp['vocalActive']
                    #self.ordre = resp['ordre']
                    #self.action = resp['action']
                    self.port = resp['port']
                    self.sumsOfFiles = resp['sumsOfFiles']
                    #self.playertts.setOrdre(self.ordre)  
                    time.sleep(1)
                    self.checkFiles()     
                    print ('ip connected : ' + ipDetect)
                    print ('Vocal active : ' + self.vocalActive.__str__())
                    break
                except Exception as e:
                    print ("erreur requete: " + ipDetect + "  =>  " + e.__str__())

            if not self.ipDetect :
                time.sleep(10)

                
    def checkFiles(self):
        #current_dir = os.path.dirname(__file__)
        #script = './resources/model_vocal/'
        #path_model_vocal = os.path.join(current_dir, script)
        for path_file in self.sumsOfFiles :
            sumOfFile = self.sumsOfFiles[path_file]
            newDirection = os.path.join(PATH_VOCAL, path_file)
            sumLocalFile = self.checkSumMd5(newDirection)
  #          print path_file +" : "+ str(sumLocalFile) +" / "+ str(sumOfFile)
            if sumLocalFile != sumOfFile :
                print (path_file + " changed.... Need new version" )
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.ipDetect, self.port + PORT_UPDATE_FILE))
                s.send(path_file)
                s.recv(1024)
                print ('Debut envoi....' + newDirection)
                with open(newDirection, 'wb') as f:
                    print ('file opened')
                    while True:
                        #print('receiving data...')
                        data = s.recv(16384)
                    #    print('data=%s', (data))
                        if not data or data == "None" or "None" in data :
                            break
                        #write data to a file
                        f.write(data)
                s.close()
                print (path_file + " downloaded" )

    def checkSumMd5(self, fileToCheck):
        md5 = hashlib.md5()
        #current_dir = os.path.dirname(__file__)
        newDirection = os.path.join(PATH_VOCAL, fileToCheck)
        sumOfFile = 0
        try:
            with open(newDirection, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk)
            sumOfFile = md5.hexdigest()        
        except Exception  :
            pass     
        return sumOfFile 

class CheckNetwork():
            
    def check_network(self):
        
        interfaces = netifaces.interfaces()
        
        for i in interfaces:
            addrs = netifaces.ifaddresses(i)
            try:
                ip = addrs[netifaces.AF_INET][0]['addr']
                macAddr = addrs[netifaces.AF_LINK][0]['addr']
                if ip != '127.0.0.1' and '192.168' in ip:
                    ipDefault = ip
                    macAddrDefault = macAddr
            except Exception : 
                pass        
        return (ipDefault,macAddrDefault)

class Ping():
    
    def __init__(self):
        self.utils =Utils()
    
    def ping(self, ipHost):    

        
        ipPingList = []
        iprange = self.utils.find('(\w+\.\w+\.\w+)', ipHost)
        
        p = [] # ip -> process
        act = 0
        nrp = 0
        err = 0
        
        for n in range(PORT_MIN_SCAN, PORT_MAX_SCAN): # start ping processes
            ip = iprange +".%d" % n
            arg = ["ping"]
            if OSDETECT == "Linux":
                arg.append("-c3")
                arg.append("-w5")
            else:   
                arg.append("-n")
                arg.append("3")
            arg.append(ip)
            p.append((ip, subprocess.Popen(arg ,stdout = subprocess.PIPE,stderr = subprocess.PIPE)))
        
        while p:
            for i, (ip, proc) in enumerate(p[:]):
                if proc.poll() is not None: # ping finished
                    p.remove((ip, proc)) # this makes it O(n**2)
        
                    if OSDETECT == "Windows":    
                        out, error = proc.communicate()
                        out = out.split('\n')
                        isCorrect = False
                        for line in out:
                            if (ip in line) & ("TTL" in line):
                                isCorrect = True
                                
                        if isCorrect:
                            ipPingList.append(ip)
                            act = act + 1
                        else:
                            err=err+1
                    elif OSDETECT == "Linux":
                        if proc.returncode == 0:
                            out, error = proc.communicate()
                            out = out.strip()
                            act = act + 1
                            ipPingList.append(ip)
                        elif proc.returncode == 2:
                            nrp=nrp+1
                        else:
                            err=err+1
            time.sleep(.04)
        
        return ipPingList

class Utils():
    
    def find(self, needle, haystack):
        match = re.search(needle, haystack)
        if match:   
            if len(match.groups()) > 1:
                return match.groups()
            elif len(match.groups()) == 1:
                return match.groups()[0]
            else:
                return "None"
        
    def cmd_exists(self, cmd):
        if self.invoke("which " + cmd + " 2>&1").find("no " + cmd) == -1:
            return True
        return False
    
    def invoke(self, cmd):
        (sin, sout) = os.popen(cmd)
        return sout.read()
   
    
if __name__ == "__main__":
    app = Connexion()
    app.scan()
