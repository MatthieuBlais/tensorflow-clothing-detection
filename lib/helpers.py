import psycopg2
import sys
import uuid
import os
from os import listdir
from os.path import isfile, join
import json

class DatabaseConnector(object):
	"""docstring for DatabaseConnector"""
	def __init__(self, connection_string=os.getenv("POSTGRESQL_DATABASE")):
		super(DatabaseConnector, self).__init__()
		self.conn_string = connection_string
		self.con = psycopg2.connect(self.conn_string)
		self.cur = self.con.cursor()
	

	def execute(self, query):
		self.cur.execute(query)
		result = self.cur.fetchall()
		return result

	def insert(self, query):
		self.cur.execute(query)

	def select_next_id(self, table):
		query="SELECT MAX(id) FROM "+table 
		self.cur.execute(query)
		results = self.cur.fetchone()
		if results[0] == None:
			return 1
		else:
			return results[0]+1

	def commit(self):
		self.con.commit()


def random_name():
	return uuid.uuid1().hex


def list_files(folder_path):
	return [join(folder_path, f) for f in listdir(folder_path) if isfile(join(folder_path, f))]

def load_data(path):
	return json.load(open(path))


class RestoreLocalAnalysis(object):
	"""docstring for RestoreLocalAnalysis"""
	def __init__(self):
		super(RestoreLocalAnalysis, self).__init__()

	def filter_pictures_already_analyzed(self, pictures, query_folder):
		already_processed = self.list_existing_urls(query_folder)
		return [ x for x in pictures if x["url"] not in already_processed]


	def list_existing_urls(self, folder):
		files = list_files(folder)
		urls = []
		for f in files:
			if "queries" in f:
				data = load_data(f)
				for image in data:
					urls.append(self.extract_url(image))
		return urls


	def extract_url(self, query):
		query = query.split("VALUES (")[1]
		query = query.split(",")[2]
		return query.strip().replace("'", "")
			
