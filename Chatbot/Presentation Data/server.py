from flask import Flask, render_template, session
from flask_socketio import SocketIO
from flask_socketio import join_room,leave_room
import Chatbot

app = Flask(__name__)
app.config['SECRET_KEY'] = 'n8gvw9nun1235nj'
socketio = SocketIO(app)
rooms_occupied=set()
rooms_free=set()
rooms=0


@app.route('/')
def show():
    return render_template('chat.html')


@socketio.on('connect')
def connected():
    global rooms 
    global rooms_free
    global rooms_occupied
    session['Chatbot'],session['intents'],message,session['type']=Chatbot.start()
    session['state']={'state':0}
    if not rooms_free:
        rooms+=1 
        rooms_occupied.add(rooms)
        session['room']=rooms 
        join_room(rooms)
    else:
        room=rooms_free.pop()
        session['room']=room 
        join_room(room)
    array=[]
    temp=[message]
    array=temp
    socketio.emit('my response',{'message':message,'array':array},to=session['room'])
    print('connect',rooms,rooms_free,rooms_occupied)


@socketio.on('disconnect')
def disconnected():
    global rooms 
    global rooms_free
    global rooms_occupied
    rooms_occupied.remove(session['room'])
    if session['room']==rooms:
        rooms-=1 
    else:
        rooms_free.add(session['room'])
    print('disconnect',rooms,rooms_free,rooms_occupied)


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    if 'message' in json:
        session['Chatbot'],session['intents'],session['f'],json['message'],session['state']=Chatbot.findresponse(session['Chatbot'],session['intents'],json['message'],session['state'],session['type'])
        for x in json['message']:
            array=[]
            temp=x.split('. ')
            array=temp
            socketio.emit('my response', {'message':x,'array':array},to=session['room'])
        if not session['f']:
            socketio.emit('quit it',to=session['room'])


if __name__ == '__main__':
    socketio.run(app, debug=True)