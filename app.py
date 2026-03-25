import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'milliy_maxfiy_kalit_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# ASOSIY SAHIFA (LOGIN/REGISTER)
@app.route('/')
def index():
    return render_template('index.html')

# LOGIN QILISH MANTIQI
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    phone = request.form.get('phone')
    role = request.form.get('role')
    
    if username and phone:
        session['username'] = username
        session['role'] = role
        return redirect(url_for('chat')) # Chat sahifasiga o'tish
    return redirect(url_for('index'))

# CHAT SAHIFASI
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html')

# XABAR ALMASHISH
@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)