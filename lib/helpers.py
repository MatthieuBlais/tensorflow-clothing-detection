import psycopg2
import sys
import uuid
import os

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