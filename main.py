# Import
from flask import Flask, render_template,request, redirect
# Menghubungkan perpustakaan database
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
# Menghubungkan SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Membuat sebuah DB
db = SQLAlchemy(app)
# Membuat sebuah tabel

class Card(db.Model):
    # Membuat kolom-kolom
    # id
    id = db.Column(db.Integer, primary_key=True)
    # Judul
    title = db.Column(db.String(100), nullable=False)
    # Deskripsi
    subtitle = db.Column(db.String(300), nullable=False)
    # Teks
    text = db.Column(db.Text, nullable=False)

    # Menampilkan objek dan id
    def __repr__(self):
        return f'<Card {self.id}>'
    

#Tugas #2. Membuat tabel User
class User(db.Model):
    # Membuat kolom-kolom
    # id
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # kolom login
    login = db.Column(db.String(100), nullable=False)

    # kolom password
    password = db.Column(db.String(30), nullable=False)

    # Menampilkan objek dan id
    def __repr__(self):
        return f'<User {self.id}>'








# Menjalankan halaman konten
@app.route('/', methods=['GET','POST'])
def login():
        error = ''
        if request.method == 'POST':
            form_login = request.form['email']
            form_password = request.form['password']
            
            #Tugas #4. Menerapkan otorisasi
            users_db = User.query.all()
            for user in users_db:
                if form_login == user.login and form_password == user.password:
                    return redirect('/index')
                else:
                    error = 'Login atau kata sandi tidak tepat'
            return render_template('login.html', error=error)

        else:
            return render_template('login.html')



@app.route('/reg', methods=['GET','POST'])
def reg():
    if request.method == 'POST':
        login= request.form['email']
        password = request.form['password']
        
        #Tugas #3. Buat agar data pengguna direkam ke dalam database
        user = User(login=login, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect('/')
    
    else:    
        return render_template('registration.html')


# Menjalankan halaman konten
@app.route('/index')
def index():
    # Menampilkan catatan-catatan dalam database
    cards = Card.query.order_by(Card.id).all()
    return render_template('index.html', cards=cards)

# Menjalankan halaman dengan entri tersebut
@app.route('/card/<int:id>')
def card(id):
    card = Card.query.get(id)

    return render_template('card.html', card=card)

# Menjalankan halaman pembuatan entri
@app.route('/create')
def create():
    return render_template('create_card.html')

# Formulir entri
@app.route('/form_create', methods=['GET','POST'])
def form_create():
    if request.method == 'POST':
        title =  request.form['title']
        subtitle =  request.form['subtitle']
        text =  request.form['text']

        # Membuat objek yang akan dikirim ke DB
        card = Card(title=title, subtitle=subtitle, text=text)

        db.session.add(card)
        db.session.commit()
        return redirect('/index')
    else:
        return render_template('create_card.html')





if __name__ == "__main__":
    app.run(debug=True)