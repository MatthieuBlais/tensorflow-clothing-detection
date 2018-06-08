from dotenv import load_dotenv
load_dotenv(".env")
import image_pool
from image_pool import ImageDownloader
from database import DatabaseInterface

import json
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CURRENT_PATH = "./"

CURRENT_LABEL = "tshirt"
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


LAYER_FOLDER = "data/layers/"+CURRENT_LABEL+"/"
PICTURE_FOLDER = "pictures/"

## FIND IMAGES IN DATABASE
db = DatabaseInterface(LAYER_FOLDER)
print("GET IMAGES")
images = db.load_pictures(LABELS[CURRENT_LABEL]["category_ids"], LABELS[CURRENT_LABEL]["subcategory_ids"])

total_image = len(images)
print("IMAGES", len(images))



## START DOWNLOADING THREAD

modulo = len(images) % 10

total_per_thread = int((total_image-modulo) / 10)


downloader = ImageDownloader(images[:total_per_thread], PICTURE_FOLDER+CURRENT_LABEL, id="a")
downloader.start()

downloader1 = ImageDownloader(images[total_per_thread:(total_per_thread*2)], PICTURE_FOLDER+CURRENT_LABEL, id="b")
downloader1.start()

downloader2 = ImageDownloader(images[(total_per_thread*2):(total_per_thread*3)], PICTURE_FOLDER+CURRENT_LABEL, id="c")
downloader2.start()

downloader3 = ImageDownloader(images[(total_per_thread*3):(total_per_thread*4)], PICTURE_FOLDER+CURRENT_LABEL, id="d")
downloader3.start()

downloader4 = ImageDownloader(images[(total_per_thread*4):(total_per_thread*5)], PICTURE_FOLDER+CURRENT_LABEL, id="e")
downloader4.start()

downloader5 = ImageDownloader(images[(total_per_thread*5):(total_per_thread*6)], PICTURE_FOLDER+CURRENT_LABEL, id="f")
downloader5.start()

downloader6 = ImageDownloader(images[(total_per_thread*6):(total_per_thread*7)], PICTURE_FOLDER+CURRENT_LABEL, id="g")
downloader6.start()

downloader7 = ImageDownloader(images[(total_per_thread*7):(total_per_thread*8)], PICTURE_FOLDER+CURRENT_LABEL, id="h")
downloader7.start()

downloader8 = ImageDownloader(images[(total_per_thread*8):(total_per_thread*9)], PICTURE_FOLDER+CURRENT_LABEL, id="i")
downloader8.start()

downloader9 = ImageDownloader(images[(total_per_thread*9):], PICTURE_FOLDER+CURRENT_LABEL, id="j")
downloader9.start()


downloader.join()
downloader1.join()
downloader2.join()
downloader3.join()
downloader4.join()
downloader5.join()
downloader6.join()
downloader7.join()
downloader8.join()
downloader9.join()
final = downloader.downloaded + downloader1.downloaded + downloader2.downloaded+ downloader3.downloaded+ downloader4.downloaded+ downloader5.downloaded+ downloader6.downloaded+ downloader7.downloaded+ downloader8.downloaded+downloader9.downloaded


with open(PICTURE_FOLDER+CURRENT_LABEL+".json", "w+") as outfile:
	json.dump(final, outfile)