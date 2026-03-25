import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room # join_room qo'shildi

app = Flask(__name__)
app.secret_key = 'milliy_chat_maxfiy_kalit'
socketio = SocketIO(app)

def bazani_yaratish():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS xabarlar (id INTEGER PRIMARY KEY AUTOINCREMENT, ism TEXT, rol TEXT, matn TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS foydalanuvchilar (id INTEGER PRIMARY KEY AUTOINCREMENT, ism TEXT UNIQUE, raqam TEXT, rol TEXT)''')
    
    # YANGI JADVAL: Shaxsiy xabarlar uchun
    cursor.execute('''CREATE TABLE IF NOT EXISTS shaxsiy_xabarlar (id INTEGER PRIMARY KEY AUTOINCREMENT, yuboruvchi TEXT, qabul_qiluvchi TEXT, matn TEXT, vaqt TEXT)''')
    
    try:
        cursor.execute("ALTER TABLE xabarlar ADD COLUMN vaqt TEXT DEFAULT ''")
    except:
        pass
        
    conn.commit()
    conn.close()

bazani_yaratish()

@app.route('/', methods=['GET', 'POST'])
def asosiy_sahifa():
    if request.method == 'POST':
        session['ism'] = request.form.get('ism')
        session['raqam'] = request.form.get('raqam')
        session['rol'] = request.form.get('role')
        
        conn = sqlite3.connect('chat.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO foydalanuvchilar (ism, raqam, rol) VALUES (?, ?, ?)", (session['ism'], session['raqam'], session['rol']))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
        return redirect(url_for('chat_sahifasi'))
    return render_template('index.html')

@app.route('/chat')
def chat_sahifasi():
    if 'ism' not in session:
        return redirect(url_for('asosiy_sahifa'))
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ism, rol, matn, vaqt FROM xabarlar")
    barcha_xabarlar = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', ism=session['ism'], rol=session['rol'], xabarlar=barcha_xabarlar)

@app.route('/ustozlar')
def ustozlar_sahifasi():
    if 'ism' not in session:
        return redirect(url_for('asosiy_sahifa'))
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ism, raqam FROM foydalanuvchilar WHERE rol='ustoz'")
    ustozlar_royxati = cursor.fetchall()
    conn.close()
    return render_template('ustozlar.html', ism=session['ism'], rol=session['rol'], ustozlar=ustozlar_royxati)

# ==========================================
# YANGI: SHAXSIY CHAT SAHIFASI
# ==========================================
@app.route('/shaxsiy/<ustoz_ismi>')
def shaxsiy_chat(ustoz_ismi):
    if 'ism' not in session:
        return redirect(url_for('asosiy_sahifa'))
    
    mening_ismim = session['ism']
    
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    # Faqat men va u gaplashgan xabarlarni tortib olamiz
    cursor.execute('''SELECT yuboruvchi, matn, vaqt FROM shaxsiy_xabarlar 
                      WHERE (yuboruvchi=? AND qabul_qiluvchi=?) OR (yuboruvchi=? AND qabul_qiluvchi=?)''', 
                   (mening_ismim, ustoz_ismi, ustoz_ismi, mening_ismim))
    xabarlar = cursor.fetchall()
    conn.close()
    
    return render_template('shaxsiy_chat.html', ism=mening_ismim, rol=session['rol'], suhbatdosh=ustoz_ismi, xabarlar=xabarlar)

@app.route('/chiqish')
def chiqish():
    session.clear()
    return redirect(url_for('asosiy_sahifa'))

# Umumiy guruh xabarlari (O'zgarishsiz)
@socketio.on('yangi_xabar')
def xabar_qabul_qilish(ma_lumot):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO xabarlar (ism, rol, matn, vaqt) VALUES (?, ?, ?, ?)", (ma_lumot['ism'], ma_lumot['rol'], ma_lumot['matn'], ma_lumot.get('vaqt', '')))
    conn.commit()
    conn.close()
    emit('xabar_tarqatish', ma_lumot, broadcast=True)

# ==========================================
# YANGI: SHAXSIY XONA JONLI ALOQASI
# ==========================================
@socketio.on('shaxsiy_xonaga_kirish')
def xonaga_kirish(data):
    # Ikkita ismdan yagona xona nomini yasaymiz (Masalan: Ali va Vali kirsayam "Ali_Vali" xonasi bo'ladi)
    ismlar = sorted([data['mening_ismim'], data['suhbatdosh']])
    xona_nomi = f"{ismlar[0]}_{ismlar[1]}"
    join_room(xona_nomi) # Odamni yopiq xonaga kiritamiz

@socketio.on('yangi_shaxsiy_xabar')
def shaxsiy_xabar_qabul(data):
    yuboruvchi = data['yuboruvchi']
    qabul_qiluvchi = data['qabul_qiluvchi']
    
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO shaxsiy_xabarlar (yuboruvchi, qabul_qiluvchi, matn, vaqt) VALUES (?, ?, ?, ?)", 
                   (yuboruvchi, qabul_qiluvchi, data['matn'], data['vaqt']))
    conn.commit()
    conn.close()
    
    ismlar = sorted([yuboruvchi, qabul_qiluvchi])
    xona_nomi = f"{ismlar[0]}_{ismlar[1]}"
    # Xabarni faqat o'sha yopiq xonadagilarga tarqatamiz
    emit('shaxsiy_xabar_tarqatish', data, room=xona_nomi)

if __name__ == '__main__':
    socketio.run(app, debug=True)
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)