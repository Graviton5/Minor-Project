import os
import json
import numpy as np
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import tensorflow as tf


class ANNClassifier:

	### Running Function
	def create(data, test=False, intents=True, labelFile='Labels', modelName='Chatbot', dictKey= '', hidden_neurons=28, epochs=200):
		dataX = []
		dataY = []
		if intents:
			for key in data:
				for sentence in data[key]['text']:
					dataX.append(sentence)
					dataY.append(key)
		else:
			for key in data[dictKey]:
				for sentence in data[dictKey][key]:
					dataX.append(sentence)
					dataY.append(key)
		model = ANNClassifier.train(dataX, dataY, hidden_neurons=hidden_neurons, alpha=1, epochs=epochs, test= test, modelName=modelName,labelFile=labelFile)



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
	def train(dataX,dataY,hidden_neurons=10, alpha=1, epochs=500, dropout=False, dropout_percent=0.5,test = False, labelFile='Labels',modelName='Chatbot'):
		words = []
		classes = list(set(dataY))
		trainX = []
		trainY = []

		ignore_words = list(string.punctuation)
		for sentence in dataX:
			w = nltk.word_tokenize(sentence)
			words.extend(w)
   
		lemmatizer = WordNetLemmatizer()
		words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
		words = list(set(words))

		for i in range(len(dataX)):
			bag = []
			outputY = [0] * len(classes)

			w = nltk.word_tokenize(dataX[i])
			w = [lemmatizer.lemmatize(wrd.lower()) for wrd in w if wrd not in ignore_words]
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
		model.save("Data/"+modelName+".h5")

		dictionary = {'words': words, "classes": classes}
		with open("Data/"+labelFile+".json",'w', encoding='utf8') as f:
			json.dump(dictionary, f, indent = 4)
		return model

	def prediction(ipstring, intents, model, labels, Threshold = 0.2):
		words = labels['words']
		classes = labels['classes']
		
		ignore_words = list(string.punctuation)

		lemmatizer = WordNetLemmatizer()
		 
		w = nltk.word_tokenize(ipstring)
		w = [lemmatizer.lemmatize(wrd.lower()) for wrd in w if wrd not in ignore_words]
		bag = []

		for wrd in words:
			bag.append(1) if wrd in w else bag.append(0)

		prediction = model.predict([bag])

		print(np.max(prediction), classes[np.argmax(prediction)], Threshold, np.max(prediction) > Threshold)
		while True:
			if np.max(prediction) >= Threshold and classes[np.argmax(prediction)] in intents:
				return [classes[np.argmax(prediction)]]
			elif (len(prediction) > 0 and classes[np.argmax(prediction)] not in intents):
				prediction = np.delete(prediction, np.argmax(prediction))
			else:
				return ['OutOfScope']

	def load_labels(labelFile='Labels'):
		with open("Data/"+labelFile+'.json', 'r', encoding='utf8') as f:
			data = json.load(f)
		return data


	def load_model(modelName='Chatbot'):
		new_model = tf.keras.models.load_model('Data/'+modelName+".h5")
		return new_model

if __name__ == '__main__':
	ip = ''

	while(ip != 'q'):
		print("Enter input: ")
		ip = input()
		print(ANNClassifier.prediction(ip))