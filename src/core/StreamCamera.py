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
 
from subprocess import Popen, PIPE
import threading

import gi
from core import PORT_STREAM_CAMERA
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject


#sudo modprobe bcm2835-v4l2
#gst-launch-1.0 v4l2src ! "video/x-raw,width=640,height=480" ! jpegenc ! rtpjpegpay ! udpsink host=192.168.1.106 port=5200
#raspivid -n -t 1000000 -h 480 -w 640 -vf -b 200000 -fps 10 -o - | gst-launch-1.0 fdsrc fd=0 ! decodebin ! video/x-raw,width=640,height=480 ! jpegenc ! rtpjpegpay ! udpsink host=192.168.1.106 port=5200
#raspivid -n -t 1000000 -h 480 -w 640  -b 200000 -fps 10 -rot 90 -hf -o - | gst-launch-1.0 fdsrc fd=0 ! decodebin !  "video/x-raw,width=640,height=480" ! jpegenc ! rtpjpegpay ! udpsink host=192.168.1.106 port=5200

class StreamCamera(threading.Thread):
    
    def __init__(self, ip_topibox):
        threading.Thread.__init__(self)
        self.pipeline = None
        self.videosrc = None
        self.videoenc = None
        self.videopay = None
        self.videosink = None
        sudo_password = '240979'
        proc = Popen(['sudo', '-S','modprobe','bcm2835-v4l2'], stdin=PIPE, stderr=PIPE,
          universal_newlines=True)
        sudo_prompt = proc.communicate(sudo_password + '\n')[1]

        print("Initializing GST Elements")
        GObject.threads_init()
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("framegrabber")

        # instantiate the camera source
        self.videosrc = Gst.ElementFactory.make("v4l2src")
#        self.videosrc.set_property("device", "/dev/video0")

        # instantiate the jpeg parser to ensure whole frames
        self.videoenc = Gst.ElementFactory.make("jpegenc")
        self.videopay = Gst.ElementFactory.make("rtpjpegpay")
        self.videosink = Gst.ElementFactory.make("udpsink")
        self.videosink.set_property("host", ip_topibox)
        self.videosink.set_property("port", PORT_STREAM_CAMERA)

        # add all the new elements to the pipeline
        print("Adding Elements to Pipeline")
        self.pipeline.add(self.videosrc)
        self.pipeline.add(self.videoenc)
        self.pipeline.add(self.videopay)
        self.pipeline.add(self.videosink)

        # link the elements in order, adding a filter to ensure correct size and framerate
        print("Linking GST Elements")
        camera1caps = Gst.Caps.from_string("video/x-raw, width=640,height=480")
        self.camerafilter1 = Gst.ElementFactory.make("capsfilter", "filter1") 
        self.camerafilter1.set_property("caps", camera1caps)
        self.pipeline.add(self.camerafilter1)
        #caps = Gst.caps_from_string("video/x-raw,width=640,height=480")
        #self.videosrc.set_property("caps", caps)

        if not Gst.Element.link(self.videosrc, self.camerafilter1):
            print("Elements could not be linked.")
            exit(-1)

        if not Gst.Element.link(self.camerafilter1, self.videoenc):
            print("Elements could not be linked.")
            exit(-1)

        if not Gst.Element.link(self.videoenc, self.videopay):
            print("Elements could not be linked.")
            exit(-1)

        if not Gst.Element.link(self.videopay, self.videosink):
            print("Elements could not be linked.")
            exit(-1)
        
        # start the video
        print("Setting Pipeline State")
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.PLAYING)

    def run(self):
        loop = GObject.MainLoop()
        loop.run()


if __name__ == "__main__":
    main = StreamCamera("192.168.1.106")
    main.start()

