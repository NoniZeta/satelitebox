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


# install requests.2.2.1 python setup.py install

import os
import pygame
import threading
import socket
import time, json
from core import PATH_TTS, PORT_TTS, TMP_FOLDER

class PlayerTTS:    
 
    ordre = []

    def __init__(self):
        file_res = os.path.join(PATH_TTS, 'messages.json')
        with open(file_res) as data_file:    
            self.messages = json.load(data_file)
        
    def setLang(self, lang):
        self.lang = lang

    def setOrdre(self, ordre):
        self.ordre = ordre

    def save(self, file, text_key):
        #TODO: download des fichiers  
        pass
    
    def play(self, text_key):   
        try: 
            fileTmp = os.path.join(PATH_TTS, text_key + ".mp3")
           
            if not os.path.exists(fileTmp):
                text = self.messages[text_key]["message"]
                self.save(fileTmp, text)
                
            self.playLocal(fileTmp)
            
        except Exception as e :
            print ("Player_TTS save : " + e.__str__())      
        
    def playLocal(self, fileTmp):
        try:
            pygame.mixer.init(18000, 16, 1, 4096)
            pygame.mixer.music.load(fileTmp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): 
                pygame.time.Clock().tick(10)
            
        except Exception as e:
            print ("Player pygame erreur : " + e.__str__())     
        finally:    
            pygame.mixer.quit()


class Player(threading.Thread):
    
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
    
    def run(self):

        while 1:
            connect = False
            while not connect:
                try :
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.s.bind(('', PORT_TTS))
                    self.s.listen(5)
            #       print 'Player : En attente du client....'
                    client, address = self.s.accept()
            #       print 'Player :  Connected by', address
                    connect = True
                except Exception as e:
#                    self.s =  None
                    print ("Player :  erreur socket : " + e.__str__())  
                    time.sleep(10)
            
            frames = []
            #print 'Player : Reception en cours'
            while 1:
                data = client.recv(4096)
                if not data: break
                frames.append(data)
    
            self.s.close()
            #print 'Player : Transformation en mp3'
            fn = os.path.join(TMP_FOLDER, "ordre.mp3")
            try:
                f = open(fn, 'wb') 
                for chunk in frames:
                    f.write(chunk)
                f.close()    
            except Exception as e:
                print ("Erreur => THREAD_ Player : constitution fichier mp3  : " + e.__str__())      
               
            self.parent.playLocal(fn)


if __name__ == "__main__":
    tts = PlayerTTS()
    tts.play('prete')
