import re
import sqlite3
import colorama 
from colorama import Fore, Style, Back
import numpy as np
import os, json, uuid
from datetime import datetime
from nltk.corpus import wordnet
import pandas as pd

### TODO ###
# CONTACT INTENT
# COURSE DETECTION
# WORDNET ### DONE
# YES/NO AGREE/DISAGRE system ### Intents Added



class Bot:
	Query = "Query"
	Contact = "Contact"
	OutOfScope = "OutOfScope"

	def __init__(self, name):
		self.name = name
		self.queryType = []
		self.flow = {}
		self.init_intents = ["Query", "Greeting", "BotEnquiry", "Contact", "TimeQuery", "NameQuery", "UnderstandQuery", "Swearing", "Thanks", "GoodBye", "CourtesyGoodBye", "Jokes", "SelfAware"]
		self.keyCol = ""
	### CHAT HANDLING ###
	def load_queries(self, filepath, queryKeyCol, queryWordsCol, queriesCol=[]):
		df = pd.read_excel("Queries/"+filepath).fillna(method='ffill', axis=0)
		try:
			# filepath = filepath.replace(" ", "_")
			keyName = queryKeyCol.replace(" ", "_")
			wordsCol = queryWordsCol.replace(" ", "_")
			self.keyCol = keyName

			sql = """CREATE TABLE IF NOT EXISTS querydetails ({} TEXT PRIMARY KEY, {} TEXT)""".format(keyName, wordsCol)
			connection = sqlite3.connect("Data/Bot.db")
			c = connection.cursor()
			c.execute(sql)

			for row in zip(df[queryKeyCol], df[queryWordsCol]):
				sql = """INSERT INTO querydetails({}, {}) VALUES ("{}","{}");""".format(keyName, wordsCol, row[0], row[1])
				c.execute(sql)
			connection.commit()

			for Col in queriesCol:
				ColName = Col.replace(" ","_")
				sql = """ALTER TABLE querydetails ADD COLUMN {} TEXT;""".format(ColName)
				c.execute(sql)

				for row in zip(df[queryKeyCol],df[Col]):
					sql = """UPDATE querydetails SET {} = "{}" WHERE {} = "{}";""".format(ColName, row[1], keyName, row[0])
					c.execute(sql)
				connection.commit()


			with open("Data/intent_words.json","r", encoding='utf8') as f:
				data = json.load(f)

				data["Queries"]["QueryNames"] = {}
				data["Queries"]["QueryTypes"] = {}

				for row in zip(df[queryKeyCol], df[queryWordsCol]):
					data["Queries"]["QueryNames"][row[0]] = list(row[1].lower().split(","))
			
			tempfile = os.path.join(os.path.dirname("Data/intent_words.json"), str(uuid.uuid4()))
			
			with open(tempfile, 'w', encoding='utf8') as f:
				json.dump(data, f, indent=4)
			
			os.rename(tempfile, "Data/intent_queries.json")
			print("QUERIES TABLE LOADED AND SAVED")
		except Exception as e:
			print("Error Occured: ", e)
		
		c.close()
		
	def load_querytypes(self, dict_words):
		data = Bot.load_data()
		data['Queries']['QueryTypes'] = dict_words

		for word in dict_words:
			self.queryType.append(word)

		with open("Data/intent_queries.json", 'w', encoding='utf8') as f:
			json.dump(data, f, indent=4)
		print("SUCCESSFULLY ADDED QUERY TYPES")

	def checkIntents(self, input, intents):
		data = self.load_data()
		intent_found = []

		data = data['intents']
		##Removing special characters
		input = re.sub(r'[^a-zA-Z0-9 \n\.]', ' ', input).lower()		
		# print(input)

		for intent in intents:
			words = data[intent]['text']
			similar_words = Bot.fetchSimilar(words)

			for word in similar_words:
				### NEED TO ADD SIMILAR WORDS TO MATCH AS WELL ###  ### DONE
				match = re.search(word.lower(),input)
				if match:
					intent_found.append(intent)
					break
		if intent_found == []:
			intent_found.append("OutOfScope")

		return list(set(intent_found))

	def load_data(self):
		if(os.path.exists("Data/Intent_queries.json")):
			filename = "Data/Intent_queries.json"
		else:
			filename = "Data/Intent_words.json"


		with open(filename, 'r', encoding='utf8') as file:
			data = json.load(file)
		# data = data['intents']
		return data


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


	def Response(self, intent):
		data = self.load_data()
		data = data['intents']
		output = Fore.GREEN + self.name + Style.RESET_ALL + ": "  + np.random.choice(data[intent]["responses"])
		output = output.replace("<BOT>", self.name)
		# output = output.replace("<COURSE>", Bot.course)
		output = output.replace("<QUERY>", Bot.Query)

		return output

	def start(self):
		print(self.Response("Intro"))


	def checkQuery(self, inputstr, checkType = True, checkName = True):
		data = self.load_data()
		queries = data["Queries"]
		qFound = [[],[]]

		if checkName:
			for qName in queries["QueryNames"]:
				for key in queries["QueryNames"][qName]:
					match = re.search(key.lower(), inputstr.lower())
					if match:
						qFound[0].append(qName)
						break

		if checkType:
			for qType in queries["QueryTypes"]:
				for key in queries["QueryTypes"][qType]:
					match = re. search(key.lower(), inputstr.lower())
					if match:
						qFound[1].append(qType)
						break

		return qFound


	def fetchQuery(self, found, key):
		connection = sqlite3.connect('Data/Bot.db')
		connection.row_factory= sqlite3.Row
		c = connection.cursor()	
		sql = """SELECT * FROM querydetails"""
		c.execute(sql)

		rowsfetched = c.fetchone()
		c.close()

		row = {}
		for key in rowsfetched.keys():
			row[key] = rowsfetched[key]

		return row


	def ResponseStr(self, string):
		outputstr = Fore.GREEN + self.name + Style.RESET_ALL + ": "  + string
		outputstr = outputstr.replace("<BOT>", self.name)
		# output = output.replace("<COURSE>", Bot.course)
		outputstr = outputstr.replace("<QUERY>", Bot.Query)
		print(outputstr)

	# def Query(input, intents):
	# 	data = Bot.load_data()
	# 	intent_found = []

	# 	##Removing special characters
	# 	input = re.sub(r'[^a-zA-Z0-9 \n\.]', ' ', input).lower()		
	# 	# print(input)
	# 	for intent in intents:
	# 		words = data[intent]['text']
	# 		similar_words = Bot.fetchSimilar(words)

	# 		for word in similar_words:
	# 			### NEED TO ADD SIMILAR WORDS TO MATCH AS WELL ###  ### DONE
	# 			match = re.search(word.lower(),input)
	# 			if match:
	# 				intent_found.append(intent)
	# 	if intent_found == []:
	# 		intent_found.append("OutOfScope")

	# 	return list(set(intent_found))

	# def ConversationFlow(intent_found, intents, UserResponse):
	# 	if "Query" in intent_found:

	# 			# Find Course
	# 			foundCourses = Bot.CourseFinder(UserResponse)
	# 			Bot.course = foundCourses[0]
	# 			# Get Query Type
	# 			queryType = Bot.Query(UserResponse, ['Criteria', 'Eligibility', 'Duration'])
	# 			if queryType == ["OutOfScope"]:
	# 				Bot.query = "all"
	# 			else:
	# 				# Using the First identified Query for now
	# 				Bot.query = queryType[0]
	# 			Bot.Response("Query")
	# 			Bot.QueryResponse(foundCourses[1])
	# 	if "Contact" in intent_found:
	# 		pass

	# 	if "TimeQuery" in intent_found:
	# 		time = Bot.timeFetch()
	# 		print("Today's Date and Time is: ", time)

	# 	else:
	# 		print(Bot.Response(intent_found[0]))
	# 	return list(set(intents))

	# def Response(intent):
	# 	data = Bot.load_data()
	# 	output = Fore.GREEN + Bot.botName + ": " + Style.RESET_ALL + np.random.choice(data[intent]["responses"])
	# 	output = output.replace("<BOT>", Bot.botName)
	# 	output = output.replace("<COURSE>", Bot.course)
	# 	output = output.replace("<QUERY>", Bot.query)

	# 	return output

	def QueryResponse(key):
		connection = sqlite3.connect('Bot.db')
		c = connection.cursor()	

		if Bot.query == 'all':
			sql = """SELECT program, duration, eligibility, criteria, scope, industryLabs FROM querydetails WHERE num = {}""".format(key)
		else:
			sql = """SELECT program, {} FROM querydetails WHERE num={}""".format(Bot.query.lower(), key)
		c.execute(sql)

		data = c.fetchall()
		print("Queries: ", data)
		c.close()

	### HELPER FUNCTIONS ###
	def getEmail(text):
		words = text.split()
		
		for word in words:
			match = re.match(r"^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$",word)
			if match:
				print(match.group())

	def timeFetch():
		return datetime.now()

	def CourseFinder(input):
		courses = Bot.fetchCourseWords()
		# for course in courses:
			
		return [courses[0][1], courses[0][0]]

	def fetchCourseWords():
		connection = sqlite3.connect('Bot.db')
		c = connection.cursor()	

		sql = """SELECT num, program, fullname FROM querydetails"""
		c.execute(sql)
		rowsfetched = c.fetchall()
		c.close()

		return rowsfetched



	# def save_table_details(dataframe):

	# 	df = pd.read_excel("Program Details.xlsx", sheet_name='Sheet2').fillna(method='ffill', axis=0)

	# 	connection = sqlite3.connect('Bot.db')
	# 	c = connection.cursor()
	# 	c.execute("""CREATE TABLE IF NOT EXISTS querydetails
	# 		(num INT PRIMARY KEY, program TEXT, duration TEXT, eligibility TEXT, criteria TEXT, scope TEXT, industryLabs TEXT, fullname TEXT)""")

	# 	num = 1
	# 	for i in range(len(df)):
	# 		row = list(df.loc[i])
	# 		for i in range(len(row)):
	# 			if row[i] == "Empty":
	# 				row[i] = ""
	# 		try:
	# 			sql = """INSERT INTO querydetails(num, program, duration, eligibility, criteria, scope, industryLabs, fullname) VALUES ({},"{}","{}","{}","{}","{}","{}","{}");""".format(num, row[0], row[1], row[2],row[3],row[4],row[5], row[6])
	# 			c.execute(sql)
	# 			num +=1
	# 		except Exception as e:
	# 			print(e)
	# 			print("Can't Insert ", end="")
	# 			print(row)
	# 	connection.commit()
	# 	c.close()
	# 	del df
	# 	print("QUERY-SPECIFIC TABLE CREATED")
	# def QueryHandler(intent_found):

	# 	for intent in intent_found:
	# 		if intent == "Contact":

	# def ResponseHandler(intents_found):
	# 	data = Bot.load_data()
	# 	responses = []
	# 	datarequired = ["Query", "QueryCriteria", "QueryEligibility", "QueryDuration", "Contact"]

	# 	for intent in intents_found:
	# 		if intent in datarequired:
	# 			continue
	# 		else:
	# 			output += np.random.choice(data[intent]["responses"])


	# 	# if len(intents) == 1:
	# 	# 	responses.append(data[intents]["responses"])
	# 	return output

# Bot.getEmail("Hello, my email is kumarnilind@gmail.com and my friend's @ is xdxdloltesting@muj.manipal.edu")

if __name__ == "__main__":
	# UserResponse = "INIT"
	# # query = "Greeting"

	# # connection = sqlite3.connect('Bot.db')
	# # c = connection.cursor()

	# # sql = """SELECT response FROM responses WHERE intent = '{}'""".format(query)
	# # c.execute(sql)

	# colorama.init()
	# # data = c.fetchall()
	# # for i in range(len(data)):
	# 	# data[i] = data[i][0]

	# # print(Fore.GREEN + "ChatBot:" + Style.RESET_ALL , np.random.choice(data))
	# print(Bot.Response("Intro"))
	# init_intents = ["Query", "Greeting", "BotEnquiry", "Contact", "TimeQuery", "NameQuery", "UnderstandQuery", "Swearing", "Thanks", "GoodBye", "CourtesyGoodBye", "Jokes", "SelfAware"]

	# while(UserResponse!= "quit"):
	# 	print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")
	# 	UserResponse = input()
	# 	intent_found = Bot.Query(input=UserResponse, intents=init_intents)
	# 	# print(intent_found)
	# 	# print(Bot.ResponseHandler(intent_found))

	# 	init_intents = Bot.ConversationFlow(intent_found, init_intents, UserResponse)

	# c.close()


	#Create a Chatbot Instance
	Chatbot = Bot("Botomatic")


	#Upload Queries Dataset (Optional)

	file = "Program Details.xlsx"
	keyCol = "Program Name"
	uniqueWordCol = "Full Name"
	queries_list = ["Eligibility", "Scope", "Admission Criteria", "Duration"]
	# Chatbot.load_queries(filepath=file, queryKeyCol=keyCol, queryWordsCol= uniqueWordCol, queriesCol= queries_list)


	#Enter similar words for query types (Optional)

	dict_words = {"all":['complete', 'everything', 'all', 'total', 'full'],
	"Course":["May I know your course?","I need to know your Course first","Can you tell me your course?""offered courses","education options"],
	"Eligibility":["Eligibility", "eligibility","admission details","admission","exam","MET","Entrance Test","Marks"], 
	"Scope":["Scope"], 
	"Admission Criteria":["course criteria","criteria","admission criteria","admission"], 
	"Duration":["duration","length of course","time of the course","help"]}
	# Chatbot.load_querytypes(dict_words)


	# Define Conversation Flow

	def ConversationFlow(Bot ,inputstr, intents, found, keyCol=""):

		if(Bot.Query in found and os.path.exists("Data/Intent_queries.json")):
			# qintents = []
			# for qtype in Bot.queryTypes:
			# 	qintents.append(qtype)
			# intents.append(qintents)
			Qfound = Bot.checkQuery(inputstr, intents)
			if len(Qfound[0]) < 1:
				Bot.ResponseStr("May I know your Course?")
				print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")
				inputstr = str(input())
				Qfound = Bot.checkQuery(inputstr, checkType=False)
			if len(Qfound[1]) < 1:
				Qfound[1].append("all")
			info = Bot.fetchQuery([Qfound[0][0]], Bot.keyCol)

			if Qfound[1][0] != "all": 
				for key in info:
					if(info[key] != "Empty"):
						Bot.ResponseStr("Info regarding " + key + " is: \n" + info[key])
			else:
				for query in qFound[1]:
					if(info[query] != "Empty"):
						Bot.ResponseStr("Info regarding " + key + " is: " + info[query])


		elif(Bot.Contact in found):
			pass
		elif(Bot.OutOfScope in found):
			pass

		else:
			print(Chatbot.Response(found[0]))

		return intents


	#Produce input nad outputs
	colorama.init()

	Chatbot.start()

	intents = Chatbot.init_intents
	intents.append(Bot.Query)
	intents.append(Bot.Contact)

	while(True):
		print(Fore.BLUE + "User: " + Style.RESET_ALL, end= "")

		inputstr = str(input())
		found = Chatbot.checkIntents(intents= intents, input=inputstr)
		intents = ConversationFlow(Chatbot, inputstr, intents, found, keyCol=keyCol)
		# print(found)

		if "GoodBye" in found:
			break

	

