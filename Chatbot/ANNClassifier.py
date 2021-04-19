import nltk
from nltk.stem.lancaster import LancasterStemmer
import os
import json
import datetime
import numpy as np
import time
from nltk.corpus import stopwords
import string
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import tensorflow as tf


class ANNClassifier:

	### Running Function
	def start(data, test=False, intents=True,):
		dataX = []
		dataY = []
		if intents:
			for key in data:
				for sentence in data[key]['text']:
					dataX.append(sentence)
					dataY.append(key)
		else:
			pass
		model = ANNClassifier.train(dataX, dataY, hidden_neurons=28, alpha=1, epochs=200, test= test)
		ANNClassifier.saveModel(model)


	### Collect Data from json file
	def collectData(filename):
		with open(filename) as f:
			data = json.load(f)

		return data
	### Create Training Data
	def training_data(data, queries=False):
		traindata = []
		if queries:
			data = data['Queries']
			for query in data["Querynames"]:
				for pattern in data["Querynames"][query]:
					traindata.append({"class":query, "pattern":pattern})
		else:
			data = data['Intents']
			for intent in data:
				for sentence in data[intent]['text']:
					traindata.append({"class":intent, "pattern": sentence})
		return traindata

	### Use bag of words and training data to produce a model in an ANN
	def train(dataX,dataY,hidden_neurons=10, alpha=1, epochs=50000, dropout=False, dropout_percent=0.5,test = False):
		words = []
		classes = list(set(dataY))
		trainX = []
		trainY = []

		# ignore_words = set(stopwords.words('english') + list(string.punctuation))
		ignore_words = list(string.punctuation)
		for sentence in dataX:
			w = nltk.word_tokenize(sentence)
			words.extend(w)

		stemmer = LancasterStemmer()    
		words = [stemmer.stem(w.lower()) for w in words if w not in ignore_words]
		words = list(set(words))

		for i in range(len(dataX)):
			bag = []
			outputY = [0] * len(classes)

			w = nltk.word_tokenize(dataX[i])
			w = [stemmer.stem(wrd.lower()) for wrd in w if wrd not in ignore_words]
			for wrd in words:
				bag.append(1) if wrd in w else bag.append(0)
			trainX.append(bag)
			outputY[classes.index(dataY[i])] = 1
			trainY.append(outputY)

		model = Sequential()
		model.add(Dense(hidden_neurons, activation='sigmoid'))
		model.add(Dense(len(classes),activation='sigmoid'))

		model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

		model.fit(trainX, trainY, epochs=epochs, batch_size=10)
		model.save("Data/Chatbot_model.h5")

		dictionary = {'words': words, "classes": classes}
		with open("Data/Labels.json",'w', encoding='utf8') as f:
			json.dump(dictionary, f, indent = 4)
		return model
	### Save model
	def saveModel(model):
		pass

	def prediction(ipstring, Threshold = 0.2):
		with open("Data/Labels.json", 'r', encoding='utf8') as f:
			data = json.load(f)

		words = data['words']
		classes = data['classes']
		new_model = tf.keras.models.load_model('Data/Chatbot_model.h5')
		ignore_words = list(string.punctuation)
		stemmer = LancasterStemmer() 
		w = nltk.word_tokenize(ipstring)
		w = [stemmer.stem(wrd.lower()) for wrd in w if wrd not in ignore_words]
		bag = []

		for wrd in words:
			bag.append(1) if wrd in w else bag.append(0)
		prediction = new_model.predict([bag])
		if np.max(prediction) > Threshold:
			return [classes[np.argmax(prediction)]]
		else:
			return ['OutOfScope']

if __name__ == '__main__':
	# data = ANNClassifier.collectData("Data/intent_ANN.json")
	# data = data['intents']
	# ANNClassifier.start(data)

	ip = ''

	while(ip != 'q'):
		print("Enter input: ")
		ip = input()
		print(ANNClassifier.prediction(ip))