
from lib.helpers import DatabaseConnector as dtb
from threading import Thread
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import random
import os
from PIL import Image
import time
import json
from shutil import copyfile

def copy_image(src, dest, keep=False):
	if not keep:
		os.rename(src, dest)
	else:
		copyfile(src, dest)


class ImageDownloader(object):
	"""docstring for ImageDownloader"""
	def __init__(self, images, image_folder, id=None):
		super(ImageDownloader, self).__init__()
		self.images = images
		self.downloaded = []
		self.isDone = False
		self.image_folder = image_folder
		self.errors = []
		self.id = id

	def start(self):
		self.t = Thread(target=self.run, args=())
		self.t.daemon = True
		self.started = True
		self.stopped = False 
		self.t.start()

	def read(self):
		return self.downloaded

	def done(self):
		return self.isDone

	def join(self):
		self.t.join()

	def set_local_mode(self, json_file):
		self.downloaded = json.load(open(json_file))
		self.isDone = True

	def run(self):
		print("Starting downloading pictures")
		counter = 0
		for image in self.images:
			if self.id:
				name = self.image_folder+"/"+str(self.id)+"_"+str(counter)+".jpg"
			else:
				name = self.image_folder+"/"+str(counter)+".jpg"
			self.download_image(image, name)
			self.downloaded.append({"url": image, "file": name})
			counter+=1
			#time.sleep(1)
			if counter % 1==0:
				print("Picture downloading", counter, len(self.images))
		self.isDone = True
		print("Downloading done")

	def errors():
		return self.errors

	def download_image(self, url, filename):
		try:
			with open(filename, 'wb') as handle:
				response = requests.get(url, stream=True, verify=False)
				if not response.ok:
					self.errors.append(url)
				for block in response.iter_content(1024):
					if not block:
						break
					handle.write(block)
		except Exception, e:
			self.errors.append(url)

def un_normalized(x, size):
	return int(round(x*size))

def crop(x,y, x2, y2, path, destination):
    # Download Image:
    try:
        im = Image.open(path)
        # Check Image Size
        im_size = im.size
        # Create Box
        box = (un_normalized(x, im_size[0]), un_normalized(y, im_size[1]),un_normalized(x2, im_size[0]),un_normalized(y2, im_size[1]))
        # Crop Image
        area = im.crop(box)
        area.save(destination,"JPEG")
        return True
    except:
        return False

def crop_object(obj, src, destination):
    # Download Image:
    try:
        im = Image.open(src)
        # Check Image Size
        im_size = im.size
        # Create Box
        box = (un_normalized(obj["xmin"], im_size[0]), un_normalized(obj["ymin"], im_size[1]),un_normalized(obj["xmax"], im_size[0]),un_normalized(obj["ymax"], im_size[1]))
        # Crop Image
        area = im.crop(box)
        print destination
        area.save(destination,"JPEG")
        return True
    except:
    	raise
    	return False

