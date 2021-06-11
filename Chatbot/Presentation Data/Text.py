import pyttsx3

engine = pyttsx3.init()
def run(msg):
    engine.save_to_file(msg , 'static/speak.mp3')
    engine.runAndWait()