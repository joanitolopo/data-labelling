from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, TranslationAnnotation, User
import json
import os
from flask import session
import csv
from flask import Response
import pandas as pd
import io
from flask import request

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Menghasilkan kunci acak

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

with app.app_context():
    admin_user = User(
        nama='admin',
        lastjob='sistem',
        login='admin@example.com',
        role='admin',
        password="pass",
        alamat="alamat"
    )
    admin_user.set_password('pass')  # Set password admin
    db.session.add(admin_user)
    db.session.commit()

# Load JSON data
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

@app.context_processor
def utility_processor():
    def find_next_unannotated_index(user_id):
        if not user_id:
            return None  # Kembalikan None jika user_id tidak ada

        for i in range(len(data['inputs'])):
            annotated = TranslationAnnotation.query.filter_by(
                input_text=data['inputs'][i],
                translation_text=data['predictions'][i],
                user_id=user_id,
                completed=True
            ).first()
            if not annotated:
                return i  # Kembalikan indeks data yang belum dianotasi
        return None  # Kembalikan None jika semua data sudah dianotasi
    return dict(find_next_unannotated_index=find_next_unannotated_index)

# sampled_indices = random.sample(range(len(data['inputs'])), 388)

# # Menyusun data baru yang hanya berisi sampel
# data = {
#     "inputs": [data['inputs'][i] for i in sampled_indices],
#     "predictions": [data['predictions'][i] for i in sampled_indices],
#     "golds": [data['golds'][i] for i in sampled_indices]
# }

# with open('sampled_human_eval.json', 'w', encoding='utf-8') as f:
#     json.dump(data, f, ensure_ascii=False, indent=4)


# admin only
# Fungsi untuk memeriksa apakah pengguna adalah admin
def is_admin():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return user and user.role == 'admin'
    return False

# Tambahkan fungsi is_admin ke context processor
@app.context_processor
def inject_functions():
    return dict(is_admin=is_admin)

# =================================================================================================
# Menjalankan halaman konten
MAX_LOGIN_ATTEMPTS = 3
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ''
    if 'login_attempts' not in session:
        session['login_attempts'] = 0
        
    if request.method == 'POST':
        form_login = request.form['email']
        form_password = request.form['password']
        form_lastjob = request.form['pekerjaan_terakhir']
        form_nama = request.form['nama']
        form_alamat = request.form['alamat']
        
        # Cek kredensial pengguna
        # user = User.query.filter_by(login=form_login, password=form_password).first()
        user = User.query.filter_by(login=form_login).first()
        if user:
            # Jika pengguna ada, cek password
            if user.check_password(form_password):
                # Login berhasil, simpan informasi ke sesi
                session['user_id'] = user.id
                session['user_name'] = user.nama
                return redirect('/index')  # Redirect ke halaman utama
            else:
                session['login_attempts'] += 1
                if session['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
                    return redirect('/forgot_password')
                error = 'Password salah. Silakan coba lagi.'
        else:
            # Jika pengguna tidak ditemukan, tambahkan pengguna baru
            new_user = User(login=form_login, password=form_password, lastjob=form_lastjob, nama=form_nama, alamat=form_alamat)
            new_user.set_password(form_password) 
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            session['user_name'] = new_user.nama
            return redirect('/index')

    return render_template('login.html', error=error)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = ''
    success = ''
    
    if request.method == 'POST':
        form_email = request.form['email']
        # form_name = request.form['nama']
        # form_lastjob = request.form['pekerjaan_terakhir']
        # form_alamat = request.form['alamat']
        form_new_password = request.form['new_password']
        
        # Cari pengguna berdasarkan email
        user = User.query.filter_by(login=form_email).first()
        if user:
            user.set_password(form_new_password)
            db.session.commit()
            success = 'Password berhasil diatur ulang. Silakan login dengan password baru.'
            return render_template('forgot_password.html', success=success)
        else:
            error = 'Email tidak ada. Silakan menggunakan Email yang sudah didaftarkan atau daftar menggunakan email baru.'
    
    return render_template('forgot_password.html', error=error)


@app.route('/logout')
def logout():
    session.clear()  # Hapus semua data sesi
    return redirect(url_for('login'))

# Homepage: Display all annotations
@app.route('/index')
def index():
    annotations = TranslationAnnotation.query.all()
    return render_template('index.html', annotations=annotations)

@app.route('/show_results')
def show_results():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Ambil semua anotasi pengguna saat ini
    annotations = TranslationAnnotation.query.filter_by(user_id=user_id).all()
    return render_template('results.html', annotations=annotations)

# Annotation form: Display input, translation, and rating form
@app.route('/annotate/<int:index>', methods=['GET', 'POST'])
def annotate(index):
    if index is None or index >= len(data['inputs']):
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Get form data
        fluency = int(request.form.get('fluency', 0))  # Default 0 jika input kosong
        adequacy = int(request.form.get('adequacy', 0))  # Default 0 jika input kosong
        user_id = session.get('user_id')  # Ambil user_id dari sesi

        if not user_id:
            return redirect(url_for('/'))  # Jika tidak ada sesi, redirect ke login

        # Cek apakah anotasi sudah ada di database
        annotation = TranslationAnnotation.query.filter_by(
            input_text=data['inputs'][index],
            translation_text=data['predictions'][index],
            user_id=user_id
        ).first()

        if annotation:
            # Jika sudah ada, perbarui statusnya
            annotation.fluency = fluency
            annotation.adequacy = adequacy
            annotation.completed = True
        else:
            # Jika belum ada, buat anotasi baru
            annotation = TranslationAnnotation(
                input_text=data['inputs'][index],
                translation_text=data['predictions'][index],
                fluency=fluency,
                adequacy=adequacy,
                user_id=user_id,
                completed=True
            )
            db.session.add(annotation)

        db.session.commit()

        # Redirect ke anotasi berikutnya
        return redirect(url_for('annotate', index=index + 1))

    # Tampilkan form anotasi
    input_text = data['inputs'][index]
    translation_text = data['predictions'][index]

    # Cek apakah anotasi ini sudah selesai oleh pengguna
    completed = TranslationAnnotation.query.filter_by(
        input_text=input_text,
        translation_text=translation_text,
        user_id=session.get('user_id'),
        completed=True
    ).first()

    # Hitung progress evaluasi
    total_evaluations = len(data['inputs'])  # Total evaluasi yang harus dilakukan
    current_evaluation = index + 1  # Evaluasi saat ini (dimulai dari 1)

    return render_template(
        'annotation.html',
        input_text=input_text,
        translation_text=translation_text,
        index=index,
        data=data,
        completed=bool(completed),  # True jika anotasi selesai
        total_evaluations=total_evaluations,  # Total evaluasi
        current_evaluation=current_evaluation  # Evaluasi saat ini
    )


@app.route('/download_csv', methods=['GET'])
def download_csv():
    # Hanya admin yang dapat mengakses
    if not is_admin():
        return redirect(url_for('index'))

    # Ambil parameter user_id dari query string
    user_id = request.args.get('user_id')

    # Ambil data anotasi berdasarkan user_id (jika ada) atau semua data
    if user_id:
        annotations = TranslationAnnotation.query.filter_by(user_id=user_id).all()
    else:
        annotations = TranslationAnnotation.query.all()

    # Siapkan data output
    output = []
    output.append(['ID', 'Input Text', 'Translation Text', 'Fluency', 'Adequacy', 'User', 'Last Job', "Alamat"])

    # Tambahkan data anotasi ke dalam output
    for annotation in annotations:
        user = User.query.get(annotation.user_id)
        user_name = user.nama if user else "Unknown"
        lastjob = user.lastjob if user else "Unknown"
        alamat = user.alamat if user else "Unknown"

        output.append([
            annotation.id,
            annotation.input_text,
            annotation.translation_text,
            annotation.fluency,
            annotation.adequacy,
            user_name,
            lastjob,
            alamat
        ])

    # Buat buffer sementara untuk menulis CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Tulis data ke buffer
    for row in output:
        writer.writerow(row)

    # Pindahkan pointer ke awal buffer
    buffer.seek(0)

    # Kirim buffer sebagai respons HTTP
    response = Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=annotations{"_user_" + user_id if user_id else "_all"}.csv'}
    )

    return response



@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('index'))  # Redirect jika bukan admin

    users = User.query.all()  # Ambil semua pengguna dari database
    annotations = []
    selected_user_id = None
    selected_user = None

    if request.method == 'POST':
        selected_user_id = request.form.get('user_id')
        if selected_user_id:
            # Ambil anotasi berdasarkan pengguna yang dipilih
            annotations = TranslationAnnotation.query.filter_by(user_id=selected_user_id).all()
            selected_user = User.query.get(selected_user_id)

    return render_template(
        'admin_dashboard.html',
        users=users,
        annotations=annotations,
        selected_user_id=selected_user_id,
        selected_user=selected_user
    )





if __name__ == '__main__':
    app.run(debug=True)