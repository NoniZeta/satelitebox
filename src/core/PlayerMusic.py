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

#gst-launch-1.0 filesrc location="12 Pink Floyd - High Hopes.mp3" ! mad ! audioconvert ! alsasink
 
import gi
from core import PORT_STREAM_MUSIC
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import threading, time

GObject.threads_init()
Gst.init(None)
 
#gst-launch-1.0 tcpserversrc host=192.168.1.107 port=5002 ! mad ! audioconvert ! alsasink

# create a pipeline and add [tcpserversrc ! mad ! audioconvert ! alsasink]

class PlayerMusic(threading.Thread): 
    
    volume = 1
    mute = False
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.player = Gst.Pipeline.new('player')
        self.source = Gst.ElementFactory.make("udpsrc")
        self.source.set_property("port", PORT_STREAM_MUSIC)
        self.queue =  Gst.ElementFactory.make("queue")
        self.queue.set_property("max-size-buffers", 0)  
        self.queue.set_property("max-size-time", 0) 
        self.queue.set_property("max-size-bytes", 0)   
        self.queue.set_property("min-threshold-time", 2000000000)   
        
        self.caps = Gst.Caps.from_string("application/x-rtp, media=(string)audio, format=(string)S32LE, layout=(string)interleaved, clock-rate=(int)44100, channels=(int)2, payload=(int)0")
        self.source.set_property("caps", self.caps)
         
        self.rtpL16depay = Gst.ElementFactory.make("rtpL16depay")
        self.playsink = Gst.ElementFactory.make("playsink")
        self.playsink.set_property("volume", self.volume)    
        self.playsink.set_property("mute", False) 
        
        self.player.add(self.source)
        self.player.add(self.queue)
        self.player.add(self.rtpL16depay)
        self.player.add(self.playsink)
        
        self.source.link(self.queue)
        self.queue.link(self.rtpL16depay)
        self.rtpL16depay.link(self.playsink)
         
        self.player.set_state(Gst.State.PLAYING)
        
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
 
        self.bus.connect('message', self.on_message)

    def run(self):    
        # enter into a mainloop
        loop = GObject.MainLoop()
        loop.run()

    def setMute(self):
        self.mute = not self.mute
        self.playsink.set_property("mute", True) 
        
    def setNoMute(self):
        self.mute = not self.mute
        self.playsink.set_property("mute", False) 

    def setVolume(self, sens = "UP", valeur = None):
        
        if valeur :
            self.volume = valeur
        
        if sens == "UP":
            self.volume = self.volume + 0.1
            if self.volume > 1 :
                self.volume = 1
        elif sens == "DOWN":     
            self.volume = self.volume - 0.1
            if self.volume < 0 :
                self.volume = 0
            
        self.playsink.set_property("volume", self.volume)    

    def on_message(self, bus, message):
        t = message.type
        #print (str(message.type))
        #if t == Gst.MessageType.EOS:
        #    self.on_next()
        #elif t == Gst.MessageType.ERROR:
        #    self.on_next()    

if __name__ == "__main__":
    player = PlayerMusic()
    player.start()
    
    while 1 :
        print (player.queue.get_property("current-level-time"))
        time.sleep(10)
    #    print 'test'
    # player.setVolume('test')    