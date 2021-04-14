import re
import sqlite3
import colorama 
from colorama import Fore, Style, Back
import numpy as np
import os, json, uuid
from datetime import datetime
from nltk.corpus import wordnet
import pandas as pd
from geopy.geocoders import Nominatim


class Bot:
	Query = "Query"
	Contact = "Contact"
	OutOfScope = "OutOfScope"
	Time = "TimeQuery"
	Location = "Location"
	init_intents = ["Query", "Location", "Greeting", "BotEnquiry", "Contact", "TimeQuery", "NameQuery", "UnderstandQuery", "Swearing", "Thanks", "GoodBye", "CourtesyGoodBye", "Jokes", "SelfAware"]
	
	def __init__(self, name):
		self.name = name
		self.queryType = []
		self.flow = {}
		self.intents = Bot.init_intents
		self.keyColumn = ""
		self.dbPath = "Data/Bot_"+name+".db"
		self.qPath = "Data/intent_queries_"+name+".json"
		self.variables = {}


	### DATA HANDLING ###
	def load_queries(self, filepath, keyCol, patternCol, queriesCol=[], overwrite=False):
		connection = sqlite3.connect(self.dbPath)
		c = connection.cursor()

		### If overwrite is true delete both files if either exist ###
		if(os.path.exists(self.dbPath) and overwrite):
			sql = "DROP table IF EXISTS queryDetails;"
			c.execute(sql)
			connection.commit()
		if(os.path.exists(self.qPath) and overwrite):
			os.remove(qPath)

		### All queries excel sheets must be in Queries folder ###
		df = pd.read_excel("Queries/"+filepath).fillna(method='ffill', axis=0)
		keyName = keyCol.replace(" ", "_")
		wordsCol = patternCol.replace(" ", "_")
	
		if (overwrite or (not os.path.exists(self.dbPath))):
			self.keyColumn = keyName

			try:
				### Create Database ###
				sql = """CREATE TABLE IF NOT EXISTS queryDetails ({} TEXT PRIMARY KEY, {} TEXT)""".format(keyName, wordsCol)
				c.execute(sql)

				### Fastest way to iterate through pandas dataframe ###
				for row in zip(df[keyCol], df[patternCol]):
					sql = """INSERT INTO queryDetails({}, {}) VALUES ("{}","{}");""".format(keyName, wordsCol, row[0], row[1])
					c.execute(sql)
				connection.commit()

				### Adding columns  and inserting values to the columns ###
				for Col in queriesCol:
					ColName = Col.replace(" ","_")
					sql = """ALTER TABLE queryDetails ADD COLUMN {} TEXT;""".format(ColName)
					c.execute(sql)

					for row in zip(df[keyCol],df[Col]):
						sql = """UPDATE queryDetails SET {} = "{}" WHERE {} = "{}";""".format(ColName, row[1], keyName, row[0])
						c.execute(sql)
					connection.commit()
				print("QUERIES TABLE LOADED AND SAVED")

			except Exception as e:
				print("Error Occured: ", e)
			c.close()

		if (overwrite or (not os.path.exists(self.qPath))):
			with open("Data/intent_words.json","r", encoding='utf8') as f:
				data = json.load(f)

				data["Queries"]["QueryNames"] = {}
				data["Queries"]["QueryTypes"] = {}

				for row in zip(df[keyCol], df[patternCol]):
					data["Queries"]["QueryNames"][row[0]] = [s.strip() for s in list(row[1].split(","))]

			### If there is an error the actual file won't  be created and the error can be identified ###
			tempfile = os.path.join(os.path.dirname("Data/intent_words.json"), str(uuid.uuid4()))
			
			with open(tempfile, 'w', encoding='utf8') as f:
				json.dump(data, f, indent=4)
			
			os.rename(tempfile, self.qPath)
			print("QUERIES ADDED TO JSON FILE")
		
	def load_querytypes(self, dict_words):
		data = self.load_data()
		data['Queries']['QueryTypes'] = dict_words

		for word in dict_words:
			self.queryType.append(word)

		with open(self.qPath, 'w', encoding='utf8') as f:
			json.dump(data, f, indent=4)
		print("SUCCESSFULLY ADDED QUERY TYPES")

	def load_data(self):
		if(os.path.exists(self.qPath)):
			filename = self.qPath
		else:
			filename = "Data/intent_words.json"


		with open(filename, 'r', encoding='utf8') as file:
			data = json.load(file)
		return data

	### IMPLEMENT ADD/REMOVE INTENT FUNCTION HERE
	### IMPLEMENT ADD/REMOVE QUERY FUNCTION HERE
	### IMPLEMENT A FUNCTION TO ADD/REMOVE VARIABLES FOR THE CHATBOT IN A DICTIONARY
	### IMPLEMENT A FUNCTION TO ADD/REMOVE QUERIES USING EXCEL SHEETS

	def selfLearnCollect(self, query, response):
		num = Bot.findMaxKey()+1
		connection = sqlite3.connect("Data/SelfLearn.db")
		c = connection.cursor()
		sql = """CREATE TABLE IF NOT EXISTS selfLearn (num INT PRIMARY KEY, query TEXT, response TEXT, intent TEXT)"""
		c.execute(sql)

		sql = """INSERT INTO selfLearn(num, query, response, intent) VALUES ({},"{}","{}", NULL);""".format(num,query,response)
		c.execute(sql)
		connection.commit()

	def saveContacts(self, email="", mobile="", sessionID = 0):
		connection = sqlite3.connect(self.dbPath)
		c = connection.cursor()

		sql = """CREATE TABLE IF NOT EXISTS contact (sessionID INT, email TEXT, mobile TEXT)"""
		c.execute(sql)

		sql = """INSERT INTO contact(sessionID, email, mobile) VALUES ({},"{}","{}");""".format(sessionID, email, mobile)
		c.execute(sql)
		connection.commit()
		print("SUCCESSFULLY SAVED")


	### PATTERN MATCHING SYSTEM  FUNCTIONS###
	def checkIntents(self, input, intents):
		data = self.load_data()
		intent_found = [""]
		temp = {}

		data = data['intents']
		##Removing special characters
		input = re.sub(r'[^a-zA-Z0-9 \n\.]', ' ', input).lower()		

		### PATTERN MATCHING APPROACH
		for intent in intents:
			words = data[intent]['text']
			similar_words = Bot.fetchSimilar(words)

			for word in similar_words:
				match = re.search(word.lower(),input)
				if match:
					if match not in temp:
						temp[intent] = 1
					else:
						temp[intent] +=1
		most = 0
		for key in temp:
			if temp[key] > most:
				intent_found[0] = key
				most = temp[key]

		### ADD OUT OF SCOPE IF LIST IS EMPTY
		if intent_found == [""]:
			intent_found[0] = "OutOfScope"

		return list(set(intent_found))

	def fetchSimilar(list_words):
		similar_words = []

		for word in list_words:
			if(len(word.split())) < 2:
				synonyms=[]
				for syn in wordnet.synsets(word):
					for lem in syn.lemmas():
						
						lem_name = re.sub(r'[^a-zA-Z0-9 \n\.]', ' ', lem.name()).lower()
						similar_words.append(lem_name)
				similar_words.append(word)

		return list(set(similar_words))

	def checkQuery(self, inputstr, checkType = True, checkName = True):
		data = self.load_data()
		queries = data["Queries"]
		qFound = [[""],[]]
		temp = {}

		if checkName:
			for qName in queries["QueryNames"]:
				for key in queries["QueryNames"][qName]:
					match = re.search(key.lower(), inputstr.lower())
					if match:
						if qName not in temp:
							temp[qName] = 1
						else:
							temp[qName] +=1

		most = 0

		for key in temp:
			if temp[key] > most:
				qFound[0][0] = key
				most = temp[key]
		temp = {}
		if checkType:
			for qType in queries["QueryTypes"]:
				for key in queries["QueryTypes"][qType]:
					match = re. search(key.lower(), inputstr.lower())
					if match:
						qFound[1][0].append(qType)
		return qFound


	def fetchQuery(self, found, key):
		try:
			connection = sqlite3.connect(self.dbPath)
			connection.row_factory= sqlite3.Row
			c = connection.cursor()	
			sql = """SELECT * FROM queryDetails WHERE {} LIKE '{}';""".format(key, found)
			c.execute(sql)

			rowsfetched = c.fetchone()
			c.close()

			row = {}

			for key in rowsfetched.keys():
				row[key] = rowsfetched[key]
			return row
		except Exception as e:
			return e


	### OUTPUT/RESPONSE FUNCTIONS
	def Response(self, intent):
		data = self.load_data()
		data = data['intents']
		output = Fore.GREEN + self.name + Style.RESET_ALL + ": "  + np.random.choice(data[intent]["responses"])
		output = output.replace("<BOT>", self.name)
		# output = output.replace("<COURSE>", Bot.course)
		output = output.replace("<QUERY>", Bot.Query)

		return output

	def botGreeting(self):
		return self.Response("Intro")

	def ResponseStr(self, string):
		outputstr = Fore.GREEN + self.name + Style.RESET_ALL + ": "  + string
		outputstr = outputstr.replace("<BOT>", self.name)
		return outputstr

	def findKey(self):
		connection = sqlite3.connect(self.dbPath)
		c = connection.cursor()

		sql = """PRAGMA table_info('queryDetails')"""

		c.execute(sql)

		rows = c.fetchall()

		for row in rows:
			if(row[-1]== 1):
				key = row[1]

		c.close()
		return key

	def findMaxKey():
		if(os.path.exists("Data/SelfLearn.db")):
			connection = sqlite3.connect("Data/SelfLearn.db")
			c = connection.cursor()
			sql = """SELECT MAX(num) FROM selfLearn;"""
			c.execute(sql)
			return int(c.fetchone()[0])
		else:
			return 0

	def Confirm(self, query, default=False):
		data = self.load_data()
		data = data['intents']

		intents = ['Agree', 'Disagree']
		found = self.checkIntents(intents= intents, input=query)

		if 'Agree' in found:
			return True
		elif 'Disagree' in found:
			return False
		else:
			return default ### If the value is out of OutOfScope, default is returned


	# def QueryResponse(key):
	# 	connection = sqlite3.connect('Bot.db')
	# 	c = connection.cursor()	

	# 	if Bot.query == 'all':
	# 		sql = """SELECT program, duration, eligibility, criteria, scope, industryLabs FROM queryDetails WHERE num = {}""".format(key)
	# 	else:
	# 		sql = """SELECT program, {} FROM queryDetails WHERE num={}""".format(Bot.query.lower(), key)
	# 	c.execute(sql)

	# 	data = c.fetchall()
	# 	print("Queries: ", data)
	# 	c.close()

	def getEmail(self,text):
		match = re.findall(r'[\w\.-]+@[\w\.-]+', text)
		if not match:
			return None
		return match[0]


	def getNumber(self,text):
		match = re.findall(r'[7-9]\d{9}', text)
		if not match:
			return None
		return match[0]


	### ACCESSORY FUNCTION 
	def timeFetch(self):
		return datetime.now()

	def getLoc(self,address):
		geolocator = Nominatim(user_agent="myGeocoder")
		location = geolocator.geocode(address)

		return location.address

if __name__ == "__main__":

	#Create a Chatbot Instance
	Chatbot = Bot("Botto")


	#Upload Queries Dataset (Optional)

	file = "Program Details.xlsx"
	keyCol = "Program Name"
	uniqueWordCol = "Full Name"
	queries_list = ["Eligibility", "Scope", "Admission Criteria", "Duration"]
	Chatbot.load_queries(filepath=file, keyCol=keyCol, patternCol= uniqueWordCol, queriesCol= queries_list, overwrite=False) ###Set overwrite = True for recreating a Dataset on each run

	#Enter similar words for query types (Optional)

	dict_words = {"all":['complete', 'everything', 'all', 'total', 'full'],
	"Course":["May I know your course?","I need to know your Course first","Can you tell me your course?""offered courses","education options"],
	"Eligibility":["Eligibility", "eligibility","admission details","admission","exam","MET","Entrance Test","Marks"], 
	"Scope":["Scope"], 
	"Admission Criteria":["course criteria","criteria","admission criteria","admission"], 
	"Duration":["duration","length of course","time of the course","help"]}


	### COMMENT THIS LINE BELOW AFTER CREATING IT FIRST TO IMPROVE THE LOAD TIMES
	Chatbot.load_querytypes(dict_words) 


	# Define Conversation Flow

	def ConversationFlow(Bot ,inputstr, intents, found, keyCol=""):
		if(Bot.Query in found and os.path.exists(self.qPath)):
			Qfound = Bot.checkQuery(inputstr)
			# Qfound = [[], []]
			if Qfound[0][0] == "":
				yield Bot.ResponseStr("May I know the full name of your Course?\n") + Fore.BLUE + "User: " + Style.RESET_ALL
				inputstr = str(input())
				Qfound = Bot.checkQuery(inputstr, checkType=False)
			else:
				yield Bot.ResponseStr("Wait, I am looking for the information for you\n")
			
			if Qfound[0][0] != "":
				if len(Qfound[1]) < 1:
					Qfound[1].append("all")

				info = Bot.fetchQuery(Qfound[0][0], Bot.findKey())

				if "all" in Qfound[1]: 
					for key in info:
						if(info[key] != "Empty" and info[key] != str(Bot.findKey()) and key != "Full_Name"):
							yield Bot.ResponseStr("Info regarding " + key + " in course  " + Qfound[0][0] + " is given below \n" + info[key] + "\n")
				else:
					for query in Qfound[1]:
						if(info[query] != "Empty"):
							yield Bot.ResponseStr("Info regarding " + query + " in " + Qfound[0][0] + " is given below \n" + info[query] + "\n")
			else:
				yield Bot.ResponseStr("Information regarding the course cant be found please try again.\n")
		elif(Bot.Contact in found):
			yield Bot.ResponseStr("Would you like to share email?\n") + Fore.BLUE + "User: " + Style.RESET_ALL
			ip = str(input())
			email = ""
			mobile = ""

			if(Bot.Confirm(ip)):
				yield Bot.ResponseStr("Please enter your email...\n") + Fore.BLUE + "User: " + Style.RESET_ALL
				email = str(input())
				email = Bot.getEmail(email)

			yield Bot.ResponseStr("Would you like to share mobile number?\n") + Fore.BLUE + "User: " + Style.RESET_ALL
			ip = str(input())

			if(Bot.Confirm(ip)):
				print(Bot.ResponseStr("Please enter your phone number (without spaces)...\n")) + Fore.BLUE + "User: " + Style.RESET_ALL
				mobile = str(input())
				mobile = Bot.getNumber(mobile)
			Bot.saveContacts(email,mobile)

		elif(Bot.Location in found):
				address = Bot.getLoc("Manipal University Jaipur")
				yield Bot.ResponseStr("MUJ address is \n"+ address)
		elif(Bot.OutOfScope in found):
			yield Bot.Response("OutOfScope") + "\n"

			###SELF LEARNING DATA COLLECTION CODE REMOVE COMMENTS TO RUN WITH OUT SELF LEARNING

			# yield Bot.ResponseStr("Would you like to contribute by providing a possible response to your previous query?") + "\n" + Fore.BLUE + "User: " + Style.RESET_ALL
			# ip = str(input())

			# if Bot.Confirm(ip, default=False):
			# 	Bot.selfLearnCollect(inputstr,ip)
			# 	yield Bot.ResponseStr("Thank you for putting effort in making me better!\n")
			# else:
			# 	yield Bot.ResponseStr("Okay, continuing to solve your queries\n")

		elif(Bot.Time in found):
			yield Bot.ResponseStr("Current time is " + str(Bot.timeFetch())) + "\n"

		else:
			yield Chatbot.Response(found[0]) + "\n"

		yield intents


	#Produce input nad outputs
	colorama.init()

	print(Chatbot.botGreeting())

	intents = Chatbot.init_intents
	intents.append(Bot.Query)
	intents.append(Bot.Contact)

	while(True):
		print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")

		inputstr = str(input())
		found = Chatbot.checkIntents(intents= intents, input=inputstr)
		for intents in ConversationFlow(Chatbot, inputstr, intents, found, keyCol=keyCol):
			if(type(intents) != list):
				print(intents, end="")
			

		if "GoodBye" in found:
			break

	

