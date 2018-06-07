from dotenv import load_dotenv
load_dotenv(".env")
from background import BackgroundSubtractor
from obj_detection import ObjectDetector
from layer import LayerExtractor
import image_pool
from image_pool import ImageDownloader
import lib.helpers as hlp
from database import DatabaseInterface
import json
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CURRENT_PATH = "./"
MODELS_PATH = "../"

CURRENT_LABEL = "skirts"
LABELS = {
	"jeans": {"category_ids": [45,56,101,122], "subcategory_ids": []}, #19000
	"tops": {"category_ids": [168,100,79], "subcategory_ids": []}, # 67000
	"shorts": {"category_ids": [52,104,81,106], "subcategory_ids": []}, #16126
	"tshirt": {"category_ids": [103,116,148,194,196,146,96], "subcategory_ids": []}, #68252
	"skirts": {"category_ids": [73,80,98], "subcategory_ids": []}, #15665
	"pants": {"category_ids": [82,178,195,83,18,84,105,121], "subcategory_ids": []}, #38081
	"outerwears": {"category_ids": [1,172,191,144,150,137,108,94,86,95,107,114,190,113], "subcategory_ids": []}, #40116
	"dresses": {"category_ids": [58,112], "subcategory_ids": []}, #82450
}
EXIT_FLAG = False
LOCAL_MODE = True


DEFAULT_ORIGINAL_PICTURE_FOLDER = CURRENT_PATH+"data/default/"
NO_BACKGROUND_PICTURE_FOLDER = CURRENT_PATH+"data/nobackground/"
OBJECT_EXTRACTION_PICTURE_FOLDER = CURRENT_PATH+"data/objects/"
LAYER_FOLDER = CURRENT_PATH+"data/layers/"+CURRENT_LABEL+"/"
LOCAL_PICTURES = CURRENT_PATH+"pictures/"

## MODELS ##
BACKGROUND_SUBTRACTOR_GRAPH_NAME = MODELS_PATH+'models/deeplab/frozen_inference_graph.pb'
OBJECT_DETECTION_GRAPH_NAME = MODELS_PATH+'models/rnn_8/frozen_inference_graph.pb'
OBJECT_DETECTION_LABELS = MODELS_PATH+'models/rnn_8/labels.pbtxt'
OBJECT_DETECTION_NUM_CLASSES = 8
LAYER_EXTRACTOR_GRAPH_NAME = MODELS_PATH+'models/inception/inception.pb'
PERSON_DETECTION_GRAPH_NAME = MODELS_PATH+'models/coco/frozen_inference_graph.pb'
PERSON_DETECTION_LABELS =MODELS_PATH+'models/coco/coco.pbtxt'
PERSON_DETECTION_NUM_CLASSES = 90


## FIND IMAGES IN DATABASE
db = DatabaseInterface(LAYER_FOLDER)
print("GET IMAGES")
sys.exit()
if LOCAL_MODE:
	downloader = ImageDownloader(images, "tmp")
	downloader.set_local_mode(LOCAL_PICTURES+CURRENT_LABEL+".json")
	total_image = len(downloader.read())
else:
	images = db.load_pictures(LABELS[CURRENT_LABEL]["category_ids"], LABELS[CURRENT_LABEL]["subcategory_ids"])
	total_image = len(images)
	print("IMAGES", len(images))
	#sys.exit()
	## START DOWNLOADING THREAD
	downloader = ImageDownloader(images, "tmp")
	downloader.start()

## LOADING BGSubtractor ##
print("Loading models")
print("- background subtractor")
backgroundSubtractorModel = BackgroundSubtractor(BACKGROUND_SUBTRACTOR_GRAPH_NAME)
print("- object detection")
objectDetectionModel = ObjectDetector(OBJECT_DETECTION_GRAPH_NAME, OBJECT_DETECTION_LABELS, OBJECT_DETECTION_NUM_CLASSES)
print("- layer extractor")
layerExtractionModel = LayerExtractor(LAYER_EXTRACTOR_GRAPH_NAME)
print("- person detector")
personDetectionModel = ObjectDetector(PERSON_DETECTION_GRAPH_NAME,PERSON_DETECTION_LABELS,PERSON_DETECTION_NUM_CLASSES)

errors = []
image_index = 0
while not EXIT_FLAG:
	downloaded_queue = downloader.read()
	if image_index>=len(downloaded_queue):
		if downloader.done():
			EXIT_FLAG = True 
			break
	current_image = downloaded_queue[image_index]

	## SAVE IMAGE 
	try:
		print("SAVING IMAGE", image_index, total_image)
		current_image["id"] = hlp.random_name()
		image_pool.copy_image(current_image["file"], DEFAULT_ORIGINAL_PICTURE_FOLDER+current_image["id"]+".jpg", keep=LOCAL_MODE)
		current_image["file"] = DEFAULT_ORIGINAL_PICTURE_FOLDER+current_image["id"]+".jpg"

		## BACKGROUND SUBSTRACTION
		print("BACKGROUND SUBSTRACTION", image_index, total_image)
		if len(personDetectionModel.run(current_image["file"],["person"]))>0:
			backgroundSubtractorModel.run(current_image["file"], NO_BACKGROUND_PICTURE_FOLDER+current_image["id"]+".jpg")
			obj_detect_picture = current_image["file"]
			print("DEEPLAB DONE",  backgroundSubtractorModel.has_person)
			if backgroundSubtractorModel.has_person:
				current_image["nobackground"] = NO_BACKGROUND_PICTURE_FOLDER+current_image["id"]+".jpg"
				obj_detect_picture = current_image["nobackground"]
			else:
				current_image["nobackground"] = "null"
		else:
			obj_detect_picture = current_image["file"]
			current_image["nobackground"] = "null"

		## OBJECT DETECTION 
		print("OBJECT DETECTION", image_index, total_image)
		objects = objectDetectionModel.run(obj_detect_picture,[CURRENT_LABEL])
		current_image["total_objects"] = len(objects)

		## LAYER EXTRACTION
		print("LAYER EXTRACTION", image_index, total_image)
		counter = 0
		for i in range(len(objects)):
			objects[i]["cropped_file"] = OBJECT_EXTRACTION_PICTURE_FOLDER+objects[i]["label"]+"/"+current_image["id"]+"_"+str(counter)+".jpg"
			image_pool.crop_object(objects[i], obj_detect_picture, objects[i]["cropped_file"])
			objects[i]["last_layer"] = layerExtractionModel.run(objects[i]["cropped_file"])
			counter+=1

		## SAVE
		print("SAVE", len(objects))
		db.save_objects(current_image, objects, local=LOCAL_MODE)
	except:
		print "ERROR"
		errors.append(downloaded_queue[image_index]["url"])
	image_index += 1
	# if image_index % 100 == 0:
	# 	db.commit()
	
db.close_layers()
# db.commit()

with open("download-errors.json", "w") as f:
	errors = errors + downloader.errors()
	json.dumps(errors, f)


