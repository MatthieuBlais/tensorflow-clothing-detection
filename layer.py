# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Simple image classification with Inception.

Run image classification with Inception trained on ImageNet 2012 Challenge data
set.

This program creates a graph from a saved GraphDef protocol buffer,
and runs inference on an input JPEG image. It outputs human readable
strings of the top 5 predictions along with their probabilities.

Change the --image_file argument to any jpg image to compute a
classification of that image.

Please see the tutorial and website for a detailed description of how
to use this script to perform image recognition.

https://tensorflow.org/tutorials/image_recognition/
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os.path
import re
import sys
import tarfile

import numpy as np
from six.moves import urllib
import tensorflow as tf
from os import listdir
import json

FLAGS = {
  "model_dir": "../models/inception/inception.pb"
}

class LayerExtractor(object):
  """docstring for LayerExtractor"""
  def __init__(self, graph_path):
    super(LayerExtractor, self).__init__()
    self.model = InceptionModel(graph_path)

  def run(self, image_path):
    return self.model.run(image_path)

class InceptionModel(object):
  """docstring for InceptionModel"""
  def __init__(self, graph_path):
    super(InceptionModel, self).__init__()
    with tf.gfile.FastGFile(graph_path, 'rb') as f:
      graph_def = tf.GraphDef()
      graph_def.ParseFromString(f.read())
      _ = tf.import_graph_def(graph_def, name='')
      self.sess = tf.Session()
      self.last_layer = self.sess.graph.get_tensor_by_name('pool_3:0')

  def run(self, image):
    image_data = tf.gfile.FastGFile(image, 'rb').read()
    features = self.sess.run(self.last_layer,{'DecodeJpeg/contents:0':image_data})
    return features[0][0][0].tolist()