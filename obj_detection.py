
import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile
import json
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
import requests
from lib.helpers import DatabaseConnector as dtb
from lib import label_map_util
from lib import visualization as vis_util
import uuid
import datetime


class ObjectDetectionRules(object):
	"""docstring for ObjectDetectionRules"""
	LABEL={
		"shorts": ['outerwears', 'tshirt', 'tops'],
		"jeans": ['outerwears', 'tshirt', 'tops'],
		"tops": ["jeans", "shorts", "pants", "skirts"],
		"person": [],
		"skirts": ['outerwears', 'tshirt', 'tops']
	}
		

class ObjectDetector(object):
	"""docstring for ObjectDetector"""
	def __init__(self, graph_path, label_path, num_class):
		super(ObjectDetector, self).__init__()
		self.model = ObjectDetectionModel(graph_path, label_path, num_class)

	def run(self, picture, expecting):
		image = Image.open(picture)
		boxes = self.model.run(image)
		expected = [] 
		others = []
		for i in range(len(boxes)):
			boxes[i]["width"] = image.size[0]
			boxes[i]["height"] = image.size[1]
			if boxes[i]["label"]["name"] in expecting:
				expected.append(boxes[i])
			if boxes[i]["label"]["name"] in [x for expected_label in expecting for x in ObjectDetectionRules.LABEL[expected_label]]:
				others.append(boxes[i])

		expected = self.format_objects(picture, expected, is_expected=True)
		others = self.format_objects(picture, others)
		expected, others = self.correct_detection(expected, others)
		if len(others)>1:
			max_confidende = -1
			tokeep = None
			for obj in others:
				if obj["confidence"]>max_confidende:
					max_confidende = obj["confidence"]
					tokeep = obj
			others = [tokeep]
		if len(expected)==0:
			return []
		return expected + others

	def format_object(self, path, box, is_expected=False):
		return { "is_expected":is_expected, "path": path, "height": box["height"], "width": box["width"], "label": box["label"]["name"], "confidence": box["label"]["value"], "ymin": box["ymin"], "ymax": box["ymax"], "xmin": box["xmin"], "xmax":box["xmax"]}

	def format_objects(self, path, boxes, keep_main=True, is_expected=False):
		objects = {}
		for box in boxes:
			obj = self.format_object(path, box, is_expected=is_expected)
			if obj["label"] not in objects.keys():
				objects[obj["label"]] = []
			objects[obj["label"]].append(obj)

		for key in objects.keys():
			max_value = -1
			indice = None
			for i in range(len(objects[key])):
				if objects[key][i]["confidence"]>max_value:
					max_value = objects[key][i]["confidence"]
					indice = i
			objects[key][indice]["is_main"]=True

		if keep_main:
			total = []
			for k in objects.keys():
				for obj in objects[k]:
					if "is_main" in obj.keys():
						total.append(obj)
		else:
			total=[]
			for k in objects.keys():
				for obj in objects[k]:
					total.append(obj)
		return total

	def correct_detection(self, expected, others):
		for i in range(len(expected)):
			for j in range(len(others)):
				if others[j]["ymin"] <= expected[i]["ymin"] and others[j]["ymax"] < expected[i]["ymax"] and others[j]["ymax"] > expected[i]["ymin"] and others[j]["ymax"]-expected[i]["ymin"]>=0.4:
					others[j] = None  
				elif others[j]["ymin"] <= expected[i]["ymin"] and others[j]["ymax"] < expected[i]["ymax"] and others[j]["ymax"] > expected[i]["ymin"] and others[j]["ymax"]-expected[i]["ymin"]>=0.1:
					expected[i]["ymin"] = expected[i]["ymin"] + (others[j]["ymax"]-expected[i]["ymin"]) / 2.0
					others[j]["ymax"] = others[j]["ymax"] - (others[j]["ymax"]-expected[i]["ymin"]) / 2.0
				elif others[j]["ymin"] >= expected[i]["ymin"] and others[j]["ymax"] < expected[i]["ymax"]:
					others[j] = None
				elif  others[j]["ymin"] >= expected[i]["ymin"] and others[j]["ymax"] >= expected[i]["ymax"] and expected[i]["ymax"] - others[j]["ymin"] >= 0.4:
					others[j] = None
				elif others[j]["ymin"] >= expected[i]["ymin"] and others[j]["ymax"] >= expected[i]["ymax"] and expected[i]["ymax"] - others[j]["ymin"] >= 0.1:
					expected[i]["ymax"] = expected[i]["ymax"] -  (expected[i]["ymax"]-others[j]["ymin"]) / 2.0
					others[j]["ymin"] = others[j]["ymin"] + (expected[i]["ymax"]-others[j]["ymin"]) / 2.0
				elif  others[j]["ymin"] <= expected[i]["ymin"] and others[j]["ymax"] >= expected[i]["ymax"]:
					others[j] = None

		expected = [x for x in expected if x != None]
		others = [x for x in others if x != None]
		return expected, others

class ObjectDetectionModel(object):
	"""docstring for ObjectDetectionModel"""
	def __init__(self, graph_path, label_path, num_class):
		super(ObjectDetectionModel, self).__init__()
		detection_graph = tf.Graph()
		with detection_graph.as_default():
			od_graph_def = tf.GraphDef()
			with tf.gfile.GFile(graph_path, 'rb') as fid:
				serialized_graph = fid.read()
				od_graph_def.ParseFromString(serialized_graph)
				tf.import_graph_def(od_graph_def, name='')
				self.sess = tf.Session(graph=detection_graph)
		self.label_map = label_map_util.load_labelmap(label_path)
		categories = label_map_util.convert_label_map_to_categories(self.label_map, max_num_classes=num_class, use_display_name=True)
		self.category_index = label_map_util.create_category_index(categories)
		# Definite input and output Tensors for detection_graph
		self.image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
		# Each box represents a part of the image where a particular object was detected.
		self.detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
		# Each score represent how level of confidence for each of the objects.
		# Score is shown on the result image, together with the class label.
		self.detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
		self.detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
		self.num_detections = detection_graph.get_tensor_by_name('num_detections:0')

	def load_image_into_numpy_array(self, image):
		(im_width, im_height) = image.size
		return np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)

	def run(self, image):
		try:
			
			image_np = self.load_image_into_numpy_array(image)
			image_np_expanded = np.expand_dims(image_np, axis=0)
			(boxes, scores, classes, num) = self.sess.run(
				[self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
				feed_dict={self.image_tensor: image_np_expanded})
			# Visualization of the results of a detection.
			boxes = vis_util.visualize_boxes_and_labels_on_image_array_2(
				image_np,
				np.squeeze(boxes),
				np.squeeze(classes).astype(np.int32),
				np.squeeze(scores),
				self.category_index,
				min_score_thresh=0.2,
				use_normalized_coordinates=True,
				line_thickness=5)
			return boxes
		except:
			raise