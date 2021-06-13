import re
import sqlite3 
import os, json, uuid
from datetime import datetime
import string
from spellchecker import SpellChecker

import numpy as np
import pandas as pd
import ANNClassifier as ANN
from nltk.corpus import stopwords, wordnet
import nltk
from nltk.stem import WordNetLemmatizer


class Bot:
	Query = "Query"
	Contact = "Contact"
	OutOfScope = "OutOfScope"
	Time = "TimeQuery"
	Location = "Location"
	init_intents = ["Query", "Greeting", "BotEnquiry", "Contact", "NameQuery", "Swearing", "Thanks", "GoodBye", "Jokes", "SelfAware"]
	
	def __init__(self, name):
		self.name = name
		self.queryType = []
		self.flow = {}
		self.intents = Bot.init_intents
		self.keyColumn = ""
		self.dbPath = "Data/Bot_"+name+".db"
		self.qPath = "Data/intent_queries_"+name+".json"
		self.variables = {}
		self.defaultQPath = "Data/intent_words.json"
		self.prepareData()


	### DATA HANDLING ###
	def prepareData(self):
		data = self.load_data()
		for intent in data['intents']:
			num = []
			for text in data['intents'][intent]["text"]:
				num.extend(text.split())
			data['intents'][intent]['vocabSize'] = len(list(set(num)))

		with open(self.qPath, 'w', encoding='utf8') as f:
			json.dump(data, f, indent=4)



	def load_queries(self, filepath, keyCol, patternCol, queriesCol=[], overwrite=True):
		connection = sqlite3.connect(self.dbPath)
		c = connection.cursor()

		### If overwrite is true delete both files if either exist ###
		if(os.path.exists(self.dbPath) and overwrite):
			sql = "DROP table IF EXISTS queryDetails;"
			c.execute(sql)
			connection.commit()

		### All queries excel sheets must be in Queries folder ###
		df = pd.read_excel("Queries/"+filepath).fillna(method='ffill', axis=0)
		keyName = keyCol.replace(" ", "_")
		wordsCol = patternCol.replace(" ", "_")

		if (overwrite or (os.path.exists(self.dbPath) == False)):
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

		if (overwrite):
			if(os.path.exists(self.qPath) and overwrite):
				os.remove(self.qPath)
			self.prepareData()

		with open(self.qPath,"r", encoding='utf8') as f:
			data = json.load(f)

			data["Queries"]["QueryNames"] = {}
			data["Queries"]["QueryTypes"] = {}

			for row in zip(df[keyCol], df[patternCol]):
				data["Queries"]["QueryNames"][row[0]] = [s.strip() for s in list(row[1].split(","))]

		# ### If there is an error the actual file won't  be created and the error can be identified ###
		with open(self.qPath, 'w', encoding='utf8') as f:
			json.dump(data, f, indent=4)

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
			filename = self.defaultQPath

		with open(filename, 'r', encoding='utf8') as file:
			data = json.load(file)
		return data

	### IMPLEMENT ADD/REMOVE INTENT FUNCTION HERE
	def modify_intents(self, add={}, remove={}):
		data = self.load_data()

		for key in add:
			data['intents'][key] = add[key]
		for key in remove:
			if key in data['intents'].keys():
				data['intents'].pop(key)

		if(os.path.exists(self.qPath)):
			filename = self.qPath
			with open(filename, 'w', encoding='utf8') as file:
				json.dump(data, file, indent=4)
		else:
			print(self.qPath, "cannot be found")

	### IMPLEMENT ADD/REMOVE QUERY FUNCTION HERE
	def modify_queries(self, add={}, remove={}):
		data = self.load_data()

		for key in add:
			data['Queries']['QueryNames'][key] = add[key]
		for key in remove:
			if key in data['Queries']['QueryNames'].keys():
				data['Queries']['QueryNames'].pop(key)

		if(os.path.exists(self.qPath)):
			filename = self.qPath
			with open(filename, 'w', encoding='utf8') as file:
				json.dump(data, file, indent=4)
		else:
			print(self.qPath, "cannot be found")

	### IMPLEMENT A FUNCTION TO ADD/REMOVE VARIABLES FOR THE CHATBOT IN A DICTIONARY ###DROPPED

	### IMPLEMENT A FUNCTION TO ADD/REMOVE QUERIES USING EXCEL SHEETS
	def modify_intents_excel(self, filename ,keyCol='', textCol='', responseCol='', textSeparator=',', respSeparator = '\n'):
		data = self.load_data()

		df = pd.read_excel("Queries/"+filename).fillna(method='ffill', axis=0)

		for row in zip(df[keyCol],df[textCol],df[responseCol]):
			if row[0] not in data['intents'].keys():
				textlist = row[1].split(textSeparator)
				for i in range(len(textlist)):
					textlist[i] = textlist[i].strip()

				resplist = row[2].split(respSeparator)
				for i in range(len(resplist)):
					resplist[i] = resplist[i].strip()

				if len(textlist) >= 5:
					data['intents'][row[0]] = {'text': textlist, 'responses': resplist}
				else:
					print("Too less sample texts in " + row[0] +" (Need at least 5)")
			else:
				print("Cannot enter "+ row[0] + " to intents, already exists")

		if(os.path.exists(self.qPath)):
			filename = self.qPath
			with open(filename, 'w', encoding='utf8') as file:
				json.dump(data, file, indent=4)
		else:
			print(self.qPath, "cannot be found")


	def selfLearnCollect(self, query, response,intent=None, probability=None):
		connection = sqlite3.connect("Data/SelfLearn.db")
		c = connection.cursor()
		sql = """CREATE TABLE IF NOT EXISTS selfLearn (num INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, response TEXT, intent TEXT, prob REAL)"""
		c.execute(sql)

		sql = """INSERT INTO selfLearn(query, response, intent) VALUES ("{}","{}", "{}");""".format(query,response, intent)
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
		return "SUCCESSFULLY SAVED"


	### PATTERN MATCHING SYSTEM  FUNCTIONS###
	def checkIntents(self, input, intents):
		data = self.load_data()
		intent_found = [""]
		temp = {}

		ignore_words = set(stopwords.words('english') + list(string.punctuation))

		lemmatizer = WordNetLemmatizer()  

		data = data['intents']
		##Removing special characters
		inputwd = nltk.word_tokenize(input)
		inputwd = [lemmatizer.lemmatize(w.lower()) for w in inputwd if w not in ignore_words]
		inputwd = list(set(inputwd))

		### PATTERN MATCHING APPROACH
		for intent in intents:
			words = data[intent]['text']
			similar_words = Bot.fetchSimilar(words)

			for word in similar_words:
				if word in inputwd:
					if intent not in temp:
						temp[intent] = 1
					else:
						temp[intent] +=1
			if intent in temp:
				temp[intent] = temp[intent]/data[intent]['vocabSize']
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
		ignore_words = set(stopwords.words('english') + list(string.punctuation))

		lemmatizer = WordNetLemmatizer()

		for word in list_words:
			wordtoken = nltk.word_tokenize(word)

			for token in wordtoken:
				for syn in wordnet.synsets(token):
					for lem in syn.lemmas():	
						lem_name = re.sub(r'[^a-zA-Z0-9 \n\.]', ' ', lem.name()).lower()
						similar_words.append(lem_name)

		similar_words.append(list_words)
		for word in similar_words:   
			word = [lemmatizer.lemmatize(w.lower()) for w in word if w not in ignore_words]
			word = list(set(word))

		return similar_words

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
					match = re.search(key.lower(), inputstr.lower())
					if match and qType not in qFound[1]:
						qFound[1].append(qType)
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
		output = np.random.choice(data[intent]["responses"])
		output = output.replace("<BOT>", self.name)
		output = output.replace("<QUERY>", Bot.Query)

		return output

	def botGreeting(self):
		return self.Response("Intro")

	def ResponseStr(self, string):
		outputstr = string
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
			return c.fetchone()[0]
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
			return default

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

	def spellCheck(self, inputstr):
		corrections = []

		spell = SpellChecker()
		mispelled = spell.unknown(inputstr.split())

		for word in mispelled:
			corrections.append((spell.correction(word), word))

		return corrections



def start():
	#Create a Chatbot Instance
	Chatbot = Bot("Botto")


	USE_PATTERN = False
	LOAD_ON_EACH_RUN = False

	if USE_PATTERN:


		file = "Program Details.xlsx"
		keyCol = "Program Name"
		uniqueWordCol = "Full Name"
		queries_list = ["Eligibility", "Scope", "Admission Criteria", "Duration"]
		Chatbot.keyCol=keyCol
		#Upload Queries Dataset (Optional)
		if LOAD_ON_EACH_RUN:
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

		
		#Produce input and outputs
		intents = Chatbot.init_intents
		intents.append(Bot.Query)
		intents.append(Bot.Contact)

		return Chatbot,intents,Chatbot.botGreeting(),[USE_PATTERN]

	else:


		Chatbot.defaultQPath = "Data/intent_ANN.json"
		Chatbot.qPath = "Data/intent_queries_ANN_" +Chatbot.name +".json"
		#Upload Queries Dataset (Optional)

		
		file = "Program Details.xlsx"
		Chatbot.keyCol= keyCol = "Program Name"
		uniqueWordCol = "Full Name"
		queries_list = ["Eligibility", "Scope", "Admission Criteria", "Duration"]

		if LOAD_ON_EACH_RUN:
			data = ANN.ANNClassifier.collectData(Chatbot.qPath)
			data = data['intents']
			Chatbot.load_queries(filepath=file, keyCol=keyCol, patternCol= uniqueWordCol, queriesCol= queries_list, overwrite=True) ###Set overwrite = True for recreating a Dataset on each run
			

			#Enter similar words for query types (Optional)

			dict_words = {"all":['complete', 'everything', 'all', 'total', 'full'],
			"Course":["May I know your course?","I need to know your Course first","Can you tell me your course?"],
			"Eligibility":["Eligibility", "eligibility","conditions to join","exam","MET","Entrance Test","Marks"], 
			"Scope":["Scope"], 
			"Admission Criteria":["course criteria","criteria","admission criteria","admission"], 
			"Duration":["duration","length of course","time of the course","help"]}


			### COMMENT THIS LINE BELOW AFTER CREATING IT FIRST TO IMPROVE THE LOAD TIMES
			Chatbot.load_querytypes(dict_words) 
			Chatbot.modify_intents_excel(filename="General Queries.xlsx" ,keyCol='Query', textCol='Questions', responseCol='Response', textSeparator=',', respSeparator = '\n')
		
		#Produce input and outputs

		intents = Chatbot.init_intents
		intents.append(Bot.Query)
		intents.append(Bot.Contact)

		
		###Add the new intents to the intents list
		df = pd.read_excel("Queries/General Queries.xlsx").fillna(method='ffill', axis=0)
		keyCol_excel = df["Query"]
		for i in keyCol_excel:
			intents.append(i)

		### Train Neural Network
		labelFile = "Labels_" + Chatbot.name
		modelFile = "Chatbot_" + Chatbot.name

		if LOAD_ON_EACH_RUN:
			Chatbot.modify_intents_excel(filename="General Queries.xlsx" ,keyCol='Query', textCol='Questions', responseCol='Response', textSeparator=',', respSeparator = '\n')
			data = ANN.ANNClassifier.collectData(Chatbot.qPath)
			data = data['intents']
			ANN.ANNClassifier.create(data, labelFile=labelFile, modelName=modelFile, epochs=250)

		data = ANN.ANNClassifier.load_labels(labelFile=labelFile)
		newmodel = ANN.ANNClassifier.load_model(modelName=modelFile)

		return Chatbot,intents,Chatbot.botGreeting(),[USE_PATTERN,newmodel,data]

def ConversationFlow_1(Bot ,inputstr, intents, found, keyCol="",state={}):
	msg=[]
	Qfound = Bot.checkQuery(inputstr, checkType=False)
	if Qfound[0][0] != "":
		if len(Qfound[1]) < 1:
			Qfound[1].append("all")
		info = Bot.fetchQuery(Qfound[0][0], Bot.findKey())
		if "all" in Qfound[1]: 
			for key in info:
				if(info[key] != "Empty" and key != str(Bot.findKey()) and key != "Full_Name"):
					msg.append( Bot.ResponseStr("Info regarding " + key + " in course  " + Qfound[0][0] + " is \n" + info[key] + "\n"))
		else:
			for query in Qfound[1]:
				query = query.replace(" ", "_")
				if(info[query] != "Empty"):
					msg.append( Bot.ResponseStr( query.replace("_"," ") + " for " + Qfound[0][0] +" is \n" + info[query] + "\n"))
	else:
		msg.append( Bot.ResponseStr("Information regarding the course cant be found please try again.\n"))
	state['state']=0
	return msg,intents,state


def ConversationFlow_21(Bot ,inputstr, intents, found, keyCol="",state={}):
	msg=[]
	state['email'] = ""
	state['mobile'] = ""
	
	if(Bot.Confirm(inputstr)):
		msg.append( Bot.ResponseStr("Please enter your email...\n") )
		state['state']=22
		return msg,intents,state
	msg.append( Bot.ResponseStr("Would you like to share mobile number?\n") )
	state['state']=23
	return msg,intents,state

def ConversationFlow_22(Bot ,inputstr, intents, found, keyCol="",state={}):
	msg=[]
	state['email'] = Bot.getEmail(inputstr)
	msg.append( Bot.ResponseStr("Would you like to share mobile number?\n") )
	state['state']=23
	return msg,intents,state


def ConversationFlow_23(Bot ,inputstr, intents, found, keyCol="",state={}):
	msg=[]
	if(Bot.Confirm(inputstr)):
		msg.append(Bot.ResponseStr("Please enter your phone number (without spaces)...\n")) 
		state['state']=24
		return msg,intents,state
	if state['email']=='':
		state['state']=0 
		msg.append('How can I help you?')
		return msg,intents,state 
	state['state']=0
	msg.append(Bot.saveContacts(state['email'],state['mobile']))
	return msg,intents,state

def ConversationFlow_24(Bot ,inputstr, intents, found, keyCol="",state={}):
	msg=[]
	state['mobile'] = Bot.getNumber(inputstr)
	msg.append(Bot.saveContacts(state['email'],state['mobile']))
	state['state']=0
	return msg,intents,state

def ConversationFlow_3(Bot ,inputstr, intents, found, keyCol="",state={}):
	ip = inputstr
	msg=[]
	if Bot.Confirm(ip, default=False):
		msg.append(Bot.ResponseStr("What would be a possible response of your Query?"))
		state['state']=31
		return msg,intents,state
	else:
		msg.append( Bot.ResponseStr("Okay, continuing to solve your queries\n"))
	state.pop('query')
	state['state']=0
	return msg,intents,state

def ConversationFlow_31(Bot ,inputstr, intents, found, keyCol="",state={}):
	msg=[]
	Bot.selfLearnCollect(state['query'],inputstr)
	msg.append( Bot.ResponseStr("Thank you for putting effort in making me better!\n"))
	state.pop('query')
	state['state']=0
	return msg,intents,state

# Define Conversation Flow
def ConversationFlow(Bot ,inputstr, intents, found, keyCol="",state={}):
	if state['state']==1:
		return ConversationFlow_1(Bot ,inputstr, intents, found, keyCol,state)
	if state['state']==21:
		return ConversationFlow_21(Bot ,inputstr, intents, found, keyCol,state)
	if state['state']==22:
		return ConversationFlow_22(Bot ,inputstr, intents, found, keyCol,state)
	if state['state']==23:
		return ConversationFlow_23(Bot ,inputstr, intents, found, keyCol,state)
	if state['state']==24:
		return ConversationFlow_24(Bot ,inputstr, intents, found, keyCol,state)
	if state['state']==3:
		return ConversationFlow_3(Bot ,inputstr, intents, found, keyCol,state)
	if state['state']==31:
		return ConversationFlow_31(Bot ,inputstr, intents, found, keyCol,state)
	msg=[]
	if(Bot.Query in found and os.path.exists(Bot.qPath)):
		Qfound = Bot.checkQuery(inputstr)
		if Qfound[0][0] == "":
			msg.append( Bot.ResponseStr("May I know the full name of your Course?\n") )
			state['state']=1
			return msg,intents,state
		else:
			msg.append( Bot.ResponseStr("Wait, I am looking for the information for you\n"))
		
		if Qfound[0][0] != "":
			if len(Qfound[1]) < 1:
				Qfound[1].append("all")
			info = Bot.fetchQuery(Qfound[0][0], Bot.findKey())

			if "all" in Qfound[1]: 
				for key in info:
					if(info[key] != "Empty" and key != str(Bot.findKey()) and key != "Full_Name"):
						msg.append(Bot.ResponseStr("Info regarding " + key + " in course  " + Qfound[0][0] + " is \n" + info[key] + "\n"))
			else:
				print(Qfound[1])
				for query in Qfound[1]:
					query = query.replace(" ", "_")
					if(info[query] != "Empty"):
						msg.append(Bot.ResponseStr( query.replace("_"," ") + " for " + Qfound[0][0] +" is \n" + info[query] + "\n"))
		else:
			msg.append( Bot.ResponseStr("Information regarding the course cant be found please try again.\n"))
	elif(Bot.Contact in found):
		msg.append( Bot.ResponseStr("Would you like to share email?\n") )
		state['state']=21
		return msg,intents,state
	elif(Bot.OutOfScope in found):
		msg.append( Bot.Response("OutOfScope") + "\n")
		###SELF LEARNING DATA COLLECTION CODE REMOVE COMMENTS TO RUN WITH OUT SELF LEARNING
		msg.append(Bot.ResponseStr("Would you like to contribute by providing a possible response to your previous query?"))
		state['state']=3
		state['query']=inputstr
		return msg,intents,state
	elif(Bot.Time in found):
		msg.append( Bot.ResponseStr("Current time is " + str(Bot.timeFetch())) + "\n")
	else:
		msg.append( Bot.Response(found[0]) + "\n")
	return  msg,intents,state

def findresponse_corrections(Chatbot,intents,user_msg,state,type):
	state['state']=0
	if type[0]:
		f=True
		msg=[]
		inputstr=state['inputstr']
		inputstr2=state['inputstr2']
		if Chatbot.Confirm(user_msg, default=False):
			inputstr = inputstr2
		found = Chatbot.checkIntents(intents= intents, input=inputstr)
		msg,intents,state=ConversationFlow(Chatbot, inputstr, intents, found, keyCol=Chatbot.keyCol,state=state)
			
		if "GoodBye" in found:
			f=False
		return Chatbot,intents,f,msg,state
	else:
		f=True
		msg=[]
		inputstr=state['inputstr']
		inputstr2=state['inputstr2']
		if Chatbot.Confirm(user_msg, default=False):
			inputstr = inputstr2
		found = ANN.ANNClassifier.prediction(inputstr, intents, model = type[1], labels=type[2])
		msg,intents,state=ConversationFlow(Chatbot, inputstr, intents, found, keyCol=Chatbot.keyCol,state=state)
			
		if "GoodBye" in found:
			f=False 
		return Chatbot,intents,f,msg,state




def findresponse(Chatbot,intents,user_msg,state,chatbot_type):
	if state['state']=="corrections":
		return findresponse_corrections(Chatbot,intents,user_msg,state,chatbot_type)
	if chatbot_type[0]:
		f=True
		msg=[]
		inputstr = user_msg

		found = Chatbot.checkIntents(intents= intents, input=inputstr)
		msg,intents,state=ConversationFlow(Chatbot, inputstr, intents, found, keyCol=Chatbot.keyCol,state=state)
			
		return Chatbot,intents,f,msg,state
	else:
		f=True
		msg=[]
		inputstr = user_msg
		
		found = ANN.ANNClassifier.prediction(inputstr, intents, model = chatbot_type[1], labels=chatbot_type[2])
		msg,intents,state=ConversationFlow(Chatbot, inputstr, intents, found, keyCol=Chatbot.keyCol,state=state)

		return Chatbot,intents,f,msg,state

