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

# from __future__ import unicode_literals

from collections import Counter
import gi
from core import PORT_VOCAL_RECEIVER, PORT_VOCAL_SENDER, PATH_VOCAL, ACOUSTIC,\
    DICTIONARY, KEYPHRASE
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

import json
import pyaudio
#import Resampler as r 
import socket
from pocketsphinx import *
from sphinxbase import *
import threading
import time

from core.Socket_bidir import SocketBidir
import os
    
gst = Gst

# Pyaudio Initialization

#FORMAT = pyaudio.paALSA

#current_dir = os.path.dirname(__file__)
#vocal = './resources/model_vocal'
#path_vocal = os.path.join(current_dir, vocal)

#key_phrase_list_file = 'keyphrase.list'
#hmmd_file = 'acoustic'
#dictp_file = 'topi.dic'

key_phrase_list = os.path.join(PATH_VOCAL, KEYPHRASE)
hmmd = os.path.join(PATH_VOCAL, ACOUSTIC)
dictp = os.path.join(PATH_VOCAL, DICTIONARY)


class StreamVocal(threading.Thread):
    
    s = None
    
    
    def __init__(self, parent):
        super(StreamVocal, self).__init__()
        self.parent = parent
        self.kill = False 
        self.playertts = self.parent.playertts
        self.p = pyaudio.PyAudio()
 #       self.resampler = r.Resampler(conf.RATE)

        self.t_start = 0
        self.t_end = 0
        self.repete_time = 0
          
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            print((i, dev['name'], dev['maxInputChannels']))

        print("Stream client init...")

        """
            CMUSphinx decoder pour le trigger "OK Jarvis"
        """
        config = Decoder.default_config()
        config.set_string('-hmm', hmmd)
        config.set_string('-dict', dictp)
        config.set_float('-kws_threshold', 1e-40)
        config.set_string('-kws', key_phrase_list)
        self.decoder = Decoder(config)
        self.decoder.start_utt()        
        
        self.sc = StreamClient()
        self.sc.start()
        
        """
            GStreamer pipeline pour recupérer le signal du micro afin de le decoder et se reveiller si une phrase de KEY_phrase_list est detecté
        """
        self.pipeline = Gst.Pipeline.new('pipeline')
        self.source = Gst.ElementFactory.make("alsasrc")
        self.audioconvert = Gst.ElementFactory.make("audioconvert")
        self.audioresample = Gst.ElementFactory.make("audioresample")
        caps = Gst.caps_from_string("audio/x-raw, rate=16000, channels=1")
        self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
        self.capsfilter.set_property("caps", caps)
        self.appsink = Gst.ElementFactory.make("appsink")
   
        self.pipeline.add(self.source)
        self.pipeline.add(self.audioconvert)
        self.pipeline.add(self.audioresample)
        self.pipeline.add(self.capsfilter)
        self.pipeline.add(self.appsink)
        
        self.source.link(self.audioconvert)
        self.audioconvert.link(self.audioresample)
        self.audioresample.link(self.capsfilter)
        self.capsfilter.link(self.appsink)
  
        self.appsink.set_property("emit-signals", True)
        self.appsink.connect("new-sample", self.new_sample)

        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop = GObject.MainLoop()
        
   
        
    def run(self):
        print("Stream client init connexion server...")
        port_sender = self.parent.port + PORT_VOCAL_RECEIVER
        port_receiver = self.parent.port + PORT_VOCAL_SENDER
        print("*** port sender   *** : " + str(port_sender))
        print("*** port receiver *** : " + str(port_receiver))
        """
            SocketBidir gère la communication entre le serveur et le satelite selon le protocole Order
        """
        self.s = SocketBidir(self.parent.ipDetect, port_receiver, port_sender, False, self.socketCallback)
        self.playertts.play('prete')

        #self.loop.run()  
        #self.pipeline.set_state(Gst.State.NULL)
        #self.createStream();
        #self.stream.start_stream()
        #self.decoder.start_utt()
        #print "Stream client running..."
        #while not self.kill:
#            try:
        #        buf = self.stream.read(12000)
        #        if not buf:
        #            break
        #        newframes, newbuf = self.resampler.resample(buf)
#                self.decoder.process_raw(newbuf, False, False)
#                hypothesis = self.decoder.hyp()
#                if hypothesis != None and hypothesis.hypstr != '': 
#                    print hypothesis.hypstr#
#                    self.decoder.end_utt() 
#                    self.stream.stop_stream()
#                    self.decode_speech()
#                    self.decoder.start_utt()
#                    self.stream.start_stream() 
        #    except Exception as e:
        #        print "erreur decode Jarvis: " + e.__str__()
        #        #[Errno 32] Broken pipe
        #        if "[Errno 32]" in e.__str__() :
        #            self.playertts.play('ordre_impossible')
        #            self.stop()
        #        if self.stream.is_stopped() :
        #            print "Redemarrage du stream"
        #            self.stream.start_stream()
        #           
        #self.p.close(self.stream)
        #self.p.terminate()

    """
        GStreamer appsink : Recupère chaque sample emit par le micro qu'on décompose en buffer
        Si une phrase de Key phrase list est detecté. PAF, on lance la suite de la procedure 
    """            
    def new_sample(self, sink):
        try :
            sample = sink.emit('pull-sample')
            buf = sample.get_buffer()
            # print str(sample.get_caps().to_string())
            data = buf.extract_dup(0, buf.get_size())
            #buf = mapinfo.data
            #buffer_.unmap(mapinfo)
            if buf:
                self.decoder.process_raw(data, False, False)
            
            hypothesis = self.decoder.hyp()
            if hypothesis :
                self.decoder.end_utt()
                self.decode_speech()
                self.decoder.start_utt()
        except Exception as e :
            print("StreamClient sat : new_sample => " + e.__str__())        
        return False    
    
    """
        Boucle de 6 secondes qui permet de capturer l'ordre via le Steamclient 
    """
    def decode_speech(self):
        print("start_utterance")
        self.s.send(key="start_utterance")
        self.t_start = time.time()
        self.t_end = self.t_start + 6
        self.sc.start_streaming()
        while self.t_start < self.t_end :
            self.t_start = time.time()

        if self.repete_time > 0 :
            self.s.send(key="repete_utterance")
            self.t_start = time.time()
            self.t_end = self.t_start + self.repete_time
            while self.t_start < self.t_end :
                self.t_start = time.time()

        self.sc.stop_streaming()
        self.s.send(key="end_utterance")
        print("end_utterance")

    """
        Methode qui permet d'arreter proprement le client
    """
    def stop(self): 
        print("Stop PipelineClient")
        try:
            self.kill = True   
            self.decoder.end_utt()
            if self.s :    
                self.s.stop()
                del self.s
            if self.sc :   
                self.sc.stop_streaming()
                del self.sc
            self.pipeline.set_state(Gst.State.NULL) 
            del self.pipeline
        except Exception as e:
            print("StreamClient : stop() " + e.__str__())      


    """
        Retour du resultat de la socket BIDIR connecté avec le serveur
        Si Key = ordre_detected alors on ajoute le temps pour capturer le son du message input 
    """
    def socketCallback(self, data):
        if data.key == "ordre_detected" :
            print(str(data))
            input_time = float(data.input_time)
            self.t_start = time.time()
            self.t_end = self.t_start + input_time
            self.repete_time = float(data.repete_time)
        if data.key == "utt_repete" :
            self.t_start = time.time()
            self.t_end = self.t_start + self.repete_time
        if data.key == "end_repete" :  
            self.t_end = self.t_start      

    #def createStream(self):
    #    self.stream = self.p.open(format=FORMAT, channels=1, rate=conf.RATE, input=True,
    #                  input_device_index=conf.DEVICE,
    #                  frames_per_buffer=12000) 

    #def closeStream(self):
    #    self.stream.close()



"""
    Thread permettant de transférer le son a décoder au serveur
    Gstreamer udpsink.
"""   
class StreamClient(threading.Thread):

    pipeline = None 

    def __init__(self):
        super(StreamClient, self).__init__()
        print("Stream client init Pipeline server...")

    def initPipeline(self):
        self.pipeline = Gst.Pipeline.new('pipeline1')
        self.source = Gst.ElementFactory.make("alsasrc")
        self.audioconvert = Gst.ElementFactory.make("audioconvert")
        self.speexenc = Gst.ElementFactory.make("speexenc")
        self.rtpspeexpay = Gst.ElementFactory.make("rtpspeexpay")
        self.udpsink = Gst.ElementFactory.make("udpsink")
        self.udpsink.set_property("host", "192.168.1.106")  
        self.udpsink.set_property("port", 1234)    
        
        self.pipeline.add(self.source)
        self.pipeline.add(self.audioconvert)
        self.pipeline.add(self.speexenc)
        self.pipeline.add(self.rtpspeexpay)
        self.pipeline.add(self.udpsink)
        
        self.source.link(self.audioconvert)
        self.audioconvert.link(self.speexenc)
        self.speexenc.link(self.rtpspeexpay) 
        self.rtpspeexpay.link(self.udpsink)    

    def run(self):
        # enter into a mainloop
        self.initPipeline()
        loop = GObject.MainLoop()
        loop.run()  
    
    def start_streaming(self):
        print("pipeline starting...")
        self.initPipeline()
        self.pipeline.set_state(gst.State.PLAYING) 
        print("pipeline started!!!")

    def stop_streaming(self):
        print("pipeline ending...")
        # if hasattr(self, "pipeline"):
        self.pipeline.set_state(gst.State.NULL)
        print("pipeline ended!!!")


    def element_message(self, bus, msg):
        pass
   #     print msg.type

    
