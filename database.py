from lib.helpers import DatabaseConnector as dtb
import json
import random
import datetime

class DatabaseInterface(object):
	"""docstring for DatabaseInterface"""
	def __init__(self, layer_folder):
		super(DatabaseInterface, self).__init__()
		self.db = dtb()
		self.layers = []
		self.layer_folder = layer_folder
		self.total_layers = 0
		self.queries=[]


	def load_pictures(self, cat_ids, subcat_ids):
		subcat_query = ""
		if len(subcat_ids)>0:
			subcat_query = "or subcategory_id in ("+",".join([str(x) for x in subcat_ids])+")"

		print "QUERY 1"
		query="SELECT id from products where category_id in ("+",".join([str(x) for x in cat_ids])+") "+subcat_query+""
		products = self.db.execute(query)
		products = ["\'"+x[0]+"\'" for x in products]

		print "QUERY 2"
		query="SELECT distinct url from images i join (SELECT id from products where category_id in ("+",".join([str(x) for x in cat_ids])+") "+subcat_query+") p on i.product_id = p.id"
		all_images = self.db.execute(query)
		all_images = [x[0] for x in all_images]

		print "QUERY 3"
		query="SELECT distinct i.url from object_detections o join (SELECT distinct url from images i join (SELECT id from products where category_id in ("+",".join([str(x) for x in cat_ids])+") "+subcat_query+") p on i.product_id = p.id) i on i.url = o.url"
		existing_images = self.db.execute(query)
		existing_images = [x[0] for x in existing_images]

		all_images = [x for x in all_images if x not in existing_images]


		# query="SELECT distinct url from images where product_id in (SELECT id from products where category_id in ("+",".join([str(x) for x in cat_ids])+") "+subcat_query+") and url not in (SELECT distinct url from object_detections)"
		# images = self.db.execute(query)
		# images = [x[0] for x in images]
		random.shuffle(all_images)
		return all_images



	def save_objects(self, picture, objects, local=False):
		# FOR ALL OBJECTS 
		for obj in objects:
			if local:
				next_id = 1
			else:
				next_id = self.db.select_next_id("object_detections")
			was_expected = "true" 
			if not obj["is_expected"]:
				was_expected="false"
			picture_no_bg = "null"
			if picture["nobackground"]!="null":
				picture_no_bg = "\'"+picture["nobackground"]+"\'"
			query="INSERT INTO object_detections (id, version, url, local_path, no_background_path, cropped_name, x_min, x_max, y_min, y_max, label, condidence, was_expected, height, width, is_validated, is_wrong, detection_date) VALUES ("+str(next_id)+", 0, \'"+picture["url"]+"\', \'"+picture['file']+"\', "+picture_no_bg+" ,\'"+obj["cropped_file"]+"\', "+str(obj["xmin"])+", "+str(obj["xmax"])+", "+str(obj["ymin"])+", "+str(obj["ymax"])+", \'"+str(obj["label"])+"\', "+str(obj["confidence"])+", "+was_expected+", "+str(obj["height"])+","+str(obj["width"])+", false, null, \'"+str(datetime.datetime.today())+"\')"
			#print query
			#self.db.insert(query)
			self.queries.append(query)
			if obj["is_expected"]:
				self.save_layer(next_id, picture["url"], obj["cropped_file"], obj["last_layer"], obj["label"])

	def save_layer(self, id, url, cropped_name, weights, label):
		self.layers.append({"id":id, "url":url, "cropped_name": cropped_name, "weights":weights,"label":label})
		self.total_layers+=1

		if self.total_layers % 1000 == 0:
			with open(self.layer_folder+'vectors_'+str(self.total_layers)+'.json', 'w') as outfile:
				json.dump(self.layers, outfile)
				self.layers = []
			with open(self.layer_folder+'queries_'+str(self.total_layers)+'.json', 'w') as outfile:
				json.dump(self.queries, outfile)
				self.queries = []

	def close_layers(self):
		with open(self.layer_folder+'vectors_'+str(self.total_layers)+'.json', 'w') as outfile:
			json.dump(self.layers, outfile)
			self.layers=[]
		with open(self.layer_folder+'queries_'+str(self.total_layers)+'.json', 'w') as outfile:
				json.dump(self.queries, outfile)
				self.queries = []

	def commit(self):
		self.db.commit()
