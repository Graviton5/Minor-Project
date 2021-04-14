
import re


# pretrained_embeddings_path = 'GoogleNews-vectors-negative300.bin'
# model = gensim.models.KeyedVectors.load_word2vec_format(pretrained_embeddings_path, binary=True)
def getEmail(text):
	match = re.findall(r'[\w\.-]+@[\w\.-]+', text)
	print(match)
	return match

def getNumber(text):
	match = re.findall(r'[7-9]\d{9}', text)
	print(match)
	return match
print(getEmail("My email is lolokwtf@gmail.com"))
print(getNumber("My phone number is +9829517088"))