# coding: utf-8

import collections
import os
try:
    import StringIO
except:
    from io import StringIO
import sys
import tarfile
import tempfile
import urllib

from IPython import display
from ipywidgets import interact
from ipywidgets import interactive
from matplotlib import gridspec
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
import collections

import tensorflow as tf

import random

if tf.__version__ < '1.5.0':
    raise ImportError('Please upgrade your tensorflow installation to v1.5.0 or newer!')

# Needed to show segmentation colormap labels
from lib import get_dataset_colormap

# In[11]:

# LABEL_NAMES = np.asarray([
#     'background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle',
#     'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog',
#     'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa',
#     'train', 'tv'
# ])

class BackgroundSubtractor(object):
    """docstring for BackgroundSubtractor"""
    def __init__(self, graph_name):
        super(BackgroundSubtractor, self).__init__()
        self.model = DeepLabModel(graph_name)
        self.has_person = False

    def extract_image(self,image, mask_array, dst):
        background = Image.new('RGB', (mask_array.shape[1],mask_array.shape[0]) , (255, 255, 255))
        foreground = image
        mask_tmp = []
        for i in range(0,len(mask_array)):
            mask_tmp.append([])
            for j in range(0, len(mask_array[i])):
                if  mask_array[i][j] == 15:
                    mask_tmp[i].append([255,255,255,0])
                    self.has_person = True
                else:
                    mask_tmp[i].append([0,0,0,255])
        if self.has_person:
            mask_tmp = np.array(mask_tmp)
            mask = Image.fromarray(mask_tmp.astype('uint8'))
            result = Image.composite(background, foreground, mask)
            result.save(dst)
            return True
        return False

    def execute(self, image_name, dst):
        try:
            orignal_im = Image.open(image_name)
        except IOError:
            print('Failed to read image from %s.' % image_path)
            return None
        #print 'running deeplab on image %s...' % image_name
        resized_im, seg_map = self.model.run(orignal_im)
        self.extract_image(resized_im, seg_map, dst)

    def run(self, src, dest):
        self.has_person = False
        #interact(self.execute, image_name=src, dst=dest)
        return self.execute(src, dest)
        

class DeepLabModel(object):
    """Class to load deeplab model and run inference."""
    
    INPUT_TENSOR_NAME = 'ImageTensor:0'
    OUTPUT_TENSOR_NAME = 'SemanticPredictions:0'
    INPUT_SIZE = 513

    def __init__(self, graph_path):
        """Creates and loads pretrained deeplab model."""
        self.graph = tf.Graph()
        with open(graph_path, "rb") as f:
            graph_def = tf.GraphDef.FromString(f.read())
        with self.graph.as_default():      
            tf.import_graph_def(graph_def, name='')
        self.sess = tf.Session(graph=self.graph)
            
    def run(self, image):
        """Runs inference on a single image.
        
        Args:
            image: A PIL.Image object, raw input image.
            
        Returns:
            resized_image: RGB image resized from original input image.
            seg_map: Segmentation map of `resized_image`.
        """
        width, height = image.size
        resize_ratio = 1.0 * self.INPUT_SIZE / max(width, height)
        target_size = (int(resize_ratio * width), int(resize_ratio * height))
        resized_image = image.convert('RGB').resize(target_size, Image.ANTIALIAS)
        batch_seg_map = self.sess.run(
            self.OUTPUT_TENSOR_NAME,
            feed_dict={self.INPUT_TENSOR_NAME: [np.asarray(resized_image)]})
        seg_map = batch_seg_map[0]
        return resized_image, seg_map