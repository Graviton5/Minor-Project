import re
import sqlite3
import colorama 
# from colorama import Fore, Style, Back
import numpy as np
import os, json, uuid
from datetime import datetime
from nltk.corpus import wordnet
import pandas as pd
# from geopy.geocoders import Nominatim
import ANNClassifier as ANN
from nltk.corpus import stopwords
import nltk
from nltk.stem.lancaster import LancasterStemmer
import string
# from textblob import TextBlob
from spellchecker import SpellChecker


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
		# if(os.path.exists(self.qPath) and overwrite):
		# 	os.remove(self.qPath)

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
		# tempfile = os.path.join(os.path.dirname(self.defaultQPath), str(uuid.uuid4()))
		
		with open(self.qPath, 'w', encoding='utf8') as f:
			json.dump(data, f, indent=4)
		
		# os.rename(tempfile, self.qPath)
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
				resplist = row[2].split(respSeparator)
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
		num = Bot.findMaxKey()+1
		connection = sqlite3.connect("Data/SelfLearn.db")
		c = connection.cursor()
		sql = """CREATE TABLE IF NOT EXISTS selfLearn (num INT PRIMARY KEY, query TEXT, response TEXT, intent TEXT, prob REAL)"""
		c.execute(sql)

		sql = """INSERT INTO selfLearn(num, query, response, intent) VALUES ({},"{}","{}", "{}", {});""".format(num,query,response, intent, probability)
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

		ignore_words = set(stopwords.words('english') + list(string.punctuation))
		# ignore_words = list(string.punctuation)
		stemmer = LancasterStemmer()    

		data = data['intents']
		##Removing special characters
		# input = re.sub(r'[^a-zA-Z0-9 \n\.]', ' ', input).lower()
		inputwd = nltk.word_tokenize(input)
		inputwd = [stemmer.stem(w.lower()) for w in inputwd if w not in ignore_words]
		inputwd = list(set(inputwd))

		### PATTERN MATCHING APPROACH
		for intent in intents:
			words = data[intent]['text']
			similar_words = Bot.fetchSimilar(words)

			for word in similar_words:
				# match = re.search(word.lower(),inputwd)
				if word in inputwd:
					if intent not in temp:
						temp[intent] = 1
					else:
						temp[intent] +=1
			if intent in temp:
				temp[intent] = temp[intent]/data[intent]['vocabSize']
		most = 0
		#print(temp)
		print(temp)
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
		# ignore_words = list(string.punctuation)
		stemmer = LancasterStemmer() 

		for word in list_words:
			wordtoken = nltk.word_tokenize(word)
			# word = [stemmer.stem(w.lower()) for w in word if w not in ignore_words]
			for token in wordtoken:
				for syn in wordnet.synsets(token):
					for lem in syn.lemmas():	
						lem_name = re.sub(r'[^a-zA-Z0-9 \n\.]', ' ', lem.name()).lower()
						similar_words.append(lem_name)

		similar_words.append(list_words)
		for word in similar_words:   
			word = [stemmer.stem(w.lower()) for w in word if w not in ignore_words]
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


	### IMPLEMENT TAGS ###
	### IMPLEMENT REPLACING OF THE TAGS ###

	### OUTPUT/RESPONSE FUNCTIONS
	def Response(self, intent):
		data = self.load_data()
		data = data['intents']
		output = np.random.choice(data[intent]["responses"])
		output = output.replace("<BOT>", self.name)
		# output = output.replace("<COURSE>", Bot.course)
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

	# def getLoc(self,address):
	# 	geolocator = Nominatim(user_agent="myGeocoder")
	# 	location = geolocator.geocode(address)

	# 	return location.address
	def spellCheck(self, inputstr):
		corrections = []
		# words = inputstr.split()
		# for word in words:
		# 	correct = TextBlob(word.lower())
		# 	if(str(correct.correct()).lower() != word.lower()):
		# 		corrections.append((str(correct.correct()),word))

		spell = SpellChecker()
		mispelled = spell.unknown(inputstr.split())

		for word in mispelled:
			corrections.append((spell.correction(word), word))

		return corrections



def start():
	#Create a Chatbot Instance
	Chatbot = Bot("Botto")


	USE_PATTERN = False

	if USE_PATTERN:


		#Upload Queries Dataset (Optional)

		file = "Program Details.xlsx"
		keyCol = "Program Name"
		uniqueWordCol = "Full Name"
		queries_list = ["Eligibility", "Scope", "Admission Criteria", "Duration"]
		Chatbot.load_queries(filepath=file, keyCol=keyCol, patternCol= uniqueWordCol, queriesCol= queries_list, overwrite=False) ###Set overwrite = True for recreating a Dataset on each run
		Chatbot.keyCol=keyCol

		#Enter similar words for query types (Optional)

		dict_words = {"all":['complete', 'everything', 'all', 'total', 'full'],
		"Course":["May I know your course?","I need to know your Course first","Can you tell me your course?""offered courses","education options"],
		"Eligibility":["Eligibility", "eligibility","admission details","admission","exam","MET","Entrance Test","Marks"], 
		"Scope":["Scope"], 
		"Admission Criteria":["course criteria","criteria","admission criteria","admission"], 
		"Duration":["duration","length of course","time of the course","help"]}


		### COMMENT THIS LINE BELOW AFTER CREATING IT FIRST TO IMPROVE THE LOAD TIMES
		Chatbot.load_querytypes(dict_words) 

		# new_intents = { "Location":{"text":["location","where","address","place"],"responses":["Location of <LOC> is ","<LOC> is at","Address of <LOC> is at"]}}
		
		#Produce input nad outputs

		intents = Chatbot.init_intents
		intents.append(Bot.Query)
		intents.append(Bot.Contact)


		# colorama.init()

		return Chatbot,intents,Chatbot.botGreeting(),[USE_PATTERN]
		'''while(True):
			print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")
			inputstr = str(input())
			# corrections = Chatbot.spellCheck(inputstr)
			# if corrections != []:
			# 	for correction in corrections:
			# 		inputstr2 = inputstr.replace(correction[1], correction[0])
			# 	print(Chatbot.ResponseStr("Did you mean "+ inputstr2 +"?"))

			# 	print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")
			# 	ip = str(input())

			# 	if Chatbot.Confirm(ip, default=False):
			# 		inputstr = inputstr2
			# 	else:
			# 		print(Chatbot.ResponseStr("Please try again"))
			# 		continue


			found = Chatbot.checkIntents(intents= intents, input=inputstr)
			for intents in ConversationFlow(Chatbot, inputstr, intents, found, keyCol=keyCol):
				if(type(intents) != list):
					print(intents, end="")
				

			if "GoodBye" in found:
				break'''
	else:


		Chatbot.defaultQPath = "Data/intent_ANN.json"
		#Upload Queries Dataset (Optional)

		file = "Program Details.xlsx"
		keyCol = "Program Name"
		uniqueWordCol = "Full Name"
		queries_list = ["Eligibility", "Scope", "Admission Criteria", "Duration"]
		Chatbot.load_queries(filepath=file, keyCol=keyCol, patternCol= uniqueWordCol, queriesCol= queries_list, overwrite=True) ###Set overwrite = True for recreating a Dataset on each run
		Chatbot.keyCol=keyCol

		#Enter similar words for query types (Optional)

		dict_words = {"all":['complete', 'everything', 'all', 'total', 'full'],
		"Course":["May I know your course?","I need to know your Course first","Can you tell me your course?"],
		"Eligibility":["Eligibility", "eligibility","admission details","admission","exam","MET","Entrance Test","Marks"], 
		"Scope":["Scope"], 
		"Admission Criteria":["course criteria","criteria","admission criteria","admission"], 
		"Duration":["duration","length of course","time of the course","help"]}


		### COMMENT THIS LINE BELOW AFTER CREATING IT FIRST TO IMPROVE THE LOAD TIMES
		Chatbot.load_querytypes(dict_words) 

		# new_intents = { "Location":{"text":["location","where","address","place"],"responses":["Location of <LOC> is ","<LOC> is at","Address of <LOC> is at"]}}
		
		#Produce input and outputs

		intents = Chatbot.init_intents
		intents.append(Bot.Query)
		intents.append(Bot.Contact)

		Chatbot.modify_intents_excel(filename="General Queries.xlsx" ,keyCol='Query', textCol='Questions', responseCol='Response', textSeparator=',', respSeparator = '\n')
		
		###Add the new intents to the intents list
		df = pd.read_excel("Queries/General Queries.xlsx").fillna(method='ffill', axis=0)
		keyCol_excel = df["Query"]
		for i in keyCol_excel:
			intents.append(i)

		intents.append("Location")
		intents.append("Owner")
		intents.append("Timings")

		### Train Neural Network
		# data = ANN.ANNClassifier.collectData(Chatbot.qPath)
		# data = data['intents']

		labelFile = "Labels_" + Chatbot.name
		modelFile = "Chatbot_" + Chatbot.name

		
		# ANN.ANNClassifier.create(data, labelFile=labelFile, modelName=modelFile, epochs=250)
		data = ANN.ANNClassifier.load_labels(labelFile=labelFile)
		
		newmodel = ANN.ANNClassifier.load_model(modelName=modelFile)

		# colorama.init()
		return Chatbot,intents,Chatbot.botGreeting(),[USE_PATTERN,newmodel,data]

		'''while(True):
			print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")
			inputstr = str(input())
			corrections = Chatbot.spellCheck(inputstr)
			if corrections != []:
				for correction in corrections:
					inputstr2 = inputstr.replace(correction[1], correction[0])
				print(Chatbot.ResponseStr("Did you mean "+ inputstr2 +"?"))

				print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")
				ip = str(input())

				if Chatbot.Confirm(ip, default=False):
					inputstr = inputstr2
				# else:
				# 	print(Chatbot.ResponseStr("Please try again"))
				# 	continue

			found = ANN.ANNClassifier.prediction(inputstr, intents, model = newmodel, labels=data)

			for intents in ConversationFlow(Chatbot, inputstr, intents, found, keyCol=keyCol):
				if(type(intents) != list):
					print(intents, end="")
				
			if "GoodBye" in found:
				break'''

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
				if(info[query] != "Empty"):
					msg.append( Bot.ResponseStr( query + " of " + Qfound[0][0] +" is \n" + info[query] + "\n"))
	else:
		msg.append( Bot.ResponseStr("Information regarding the course cant be found please try again.\n"))
	state['state']=0
	return msg,intents,state


def ConversationFlow_21(Bot ,inputstr, intents, found, keyCol="",state={}):
	msg=[]
	state['email'] = ""
	state['mobile'] = ""
	
	print(Bot.Confirm(inputstr))
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
	print(Bot.Confirm(inputstr))
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
	msg=[]
	if(Bot.Query in found and os.path.exists(Bot.qPath)):
		Qfound = Bot.checkQuery(inputstr)
		# Qfound = [[], []]
		if Qfound[0][0] == "":
			msg.append( Bot.ResponseStr("May I know the full name of your Course?\n") )
			state['state']=1
			return msg,intents,state
			#Qfound = Bot.checkQuery(inputstr, checkType=False)
		else:
			msg.append( Bot.ResponseStr("Wait, I am looking for the information for you\n"))
		
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
					if(info[query] != "Empty"):
						msg.append( Bot.ResponseStr( query + " of " + Qfound[0][0] +" is \n" + info[query] + "\n"))
		else:
			msg.append( Bot.ResponseStr("Information regarding the course cant be found please try again.\n"))
	elif(Bot.Contact in found):
		msg.append( Bot.ResponseStr("Would you like to share email?\n") )
		state['state']=21
		return msg,intents,state
	# elif(Bot.Location in found):
	# 		address = Bot.getLoc("Manipal University Jaipur")
	# 		msg.append( Bot.ResponseStr("MUJ address is \n"+ address))
	elif(Bot.OutOfScope in found):
		msg.append( Bot.Response("OutOfScope") + "\n")
		###SELF LEARNING DATA COLLECTION CODE REMOVE COMMENTS TO RUN WITH OUT SELF LEARNING
		# msg.append( Bot.ResponseStr("Would you like to contribute by providing a possible response to your previous query?") + "\n" + Fore.BLUE + "User: " + Style.RESET_ALL)
		# ip = str(input())
		# if Bot.Confirm(ip, default=False):
		# 	Bot.selfLearnCollect(inputstr,ip)
		# 	msg.append( Bot.ResponseStr("Thank you for putting effort in making me better!\n"))
		# else:
		# 	msg.append( Bot.ResponseStr("Okay, continuing to solve your queries\n"))
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
		# else:
		# 	print(Chatbot.ResponseStr("Please try again"))
		# 	continue
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
		# else:
		# 	print(Chatbot.ResponseStr("Please try again"))
		# 	continue
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
		'''corrections = Chatbot.spellCheck(inputstr)
		if corrections != []:
			for correction in corrections:
				inputstr2 = inputstr.replace(correction[1], correction[0])
			msg.append(Chatbot.ResponseStr("Did you mean "+ inputstr2 +"?"))
			state['state']='corrections'
			state['inputstr']=inputstr
			state['inputstr2']=inputstr2
			return Chatbot,intents,f,msg,state
			#if Chatbot.Confirm(ip, default=False):
			#	inputstr = inputstr2
			# else:
			# 	print(Chatbot.ResponseStr("Please try again"))
			# 	continue'''
		found = Chatbot.checkIntents(intents= intents, input=inputstr)
		msg,intents,state=ConversationFlow(Chatbot, inputstr, intents, found, keyCol=Chatbot.keyCol,state=state)
			
		if "GoodBye" in found:
			f=False
		return Chatbot,intents,f,msg,state
	else:
		f=True
		msg=[]
		inputstr = user_msg
		# corrections = Chatbot.spellCheck(inputstr)
		# if corrections != []:
		# 	for correction in corrections:
		# 		inputstr2 = inputstr.replace(correction[1], correction[0])
		# 	msg.append(Chatbot.ResponseStr("Did you mean "+ inputstr2 +"?"))
		# 	state['state']="corrections"
		# 	state['inputstr']=inputstr
		# 	state['inputstr2']=inputstr2
		# 	return Chatbot,intents,f,msg,state
		# 	if Chatbot.Confirm(ip, default=False):
		# 		inputstr = inputstr2
		# 	else:
		# 		print(Chatbot.ResponseStr("Please try again"))
		# 		continue
		found = ANN.ANNClassifier.prediction(inputstr, intents, model = chatbot_type[1], labels=chatbot_type[2])
		msg,intents,state=ConversationFlow(Chatbot, inputstr, intents, found, keyCol=Chatbot.keyCol,state=state)
		if "GoodBye" in found:
			f=False 
		return Chatbot,intents,f,msg,state

