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

import os

"""
    Paramètres par defaut 
"""
LANG = 'fr'

"""
    Path
"""
CURRENT_DIR     = os.path.dirname(__file__)
PATH_RESOURCES  = os.path.join(CURRENT_DIR, "..", "..", "resources")
PATH_VOCAL      = os.path.join(PATH_RESOURCES, LANG, "model_vocal")
PATH_TTS        = os.path.join(PATH_RESOURCES, LANG, "tts")
HOME_DIR        = os.path.expanduser("~")

TMP_FOLDER= os.path.join(HOME_DIR, ".cache/topibox_tmp/")

LOG_FILE = os.path.join(TMP_FOLDER, "sateliteBox.log")

if not os.path.exists(TMP_FOLDER):
    os.makedirs(TMP_FOLDER)


PORT_HTTP                = 7002
PORT_CONTROL_SAT_CONNECT = 50000
PORT_TTS                 = 50001
PORT_STREAM_MUSIC        = 50002
PORT_STREAM_CAMERA       = 50003
PORT_VOCAL_SENDER        = 2
PORT_VOCAL_RECEIVER      = 3   
PORT_UPDATE_FILE         = 5

KWS_THRESHOLD    = 1e-40

PORT_MIN_SCAN = 1
PORT_MAX_SCAN = 200

RECORD_SECONDS = 3
RATE = 48000
DEVICE = 4  #  3 : Raspberry
            #  2 : firefly USB / 
            #  0 : firefly Carte
            #  4 : Noni Portable
            #  0 : PC

"""
    Fichiers du modele vocal 
"""

KEYPHRASE                           = "keyphrase.list"
MODEL_LM_VOCAL                      = "custom.lm.bin" 
DICTIONARY                          = "custom.dic"  
ACOUSTIC                            = "acoustic" 
ACOUSTIC_MODEL_README               = os.path.join(ACOUSTIC, "README")
ACOUSTIC_MODEL_LICENSE              = os.path.join(ACOUSTIC, "LICENSE")
ACOUSTIC_MODEL_FEAT_PARAMS          = os.path.join(ACOUSTIC, "feat.params")
ACOUSTIC_MODEL_MDEF                 = os.path.join(ACOUSTIC, "mdef")
ACOUSTIC_MODEL_MEANS                = os.path.join(ACOUSTIC, "means")
ACOUSTIC_MODEL_MIXTURE_WEIGHTS      = os.path.join(ACOUSTIC, "mixture_weights")
ACOUSTIC_MODEL_NOISEDICT            = os.path.join(ACOUSTIC, "noisedict")
#ACOUSTIC_MODEL_SENDUMP              = os.path.join(ACOUSTIC, "acoustic/sendump")
ACOUSTIC_MODEL_TRANSITION_MATRICES  = os.path.join(ACOUSTIC, "transition_matrices")
ACOUSTIC_MODEL_VARIANCES            = os.path.join(ACOUSTIC, "variances")
