from flask import Flask, session, send_from_directory, request, abort, render_template, redirect, url_for
import os, logging, owners
from functools import wraps

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'files')  # папка, где хранятся файлы
app.secret_key = 'ваш_секретный_ключ' # ключ для кук
tech_dir = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(UPLOAD_FOLDER): # создание папки
    os.makedirs(UPLOAD_FOLDER)

def valid_login(username, password): #логика авторизации
    file_data = os.path.join(tech_dir, 'static/data.txt')
    with open(file_data, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            n, p = line.split(":", 1)
            if n == username:
                if p == password:
                    return True
                else:
                    return False
    return False

def check(f):                    #логика проверки авторизации
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def log_the_user_in():
    return redirect('/')

@app.route('/error') #тестовая ошибка
def error():
    # Искусственная ошибка
    1/0

@app.route('/')#Главная страница
@check
def home():
    user_name = session.get('user_id')
    return render_template('index.html', username=user_name)

@app.route('/download/<filename>')
@check
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True) #страница скачивания

@app.route('/files')#страница просмотра файлов
@check
def divide_files():
    user_name = session.get('user_id')
    allowed_files = owners.sel_f(user_name)
    print(allowed_files)
    #files = os.listdir(UPLOAD_FOLDER)  # Получаем список файлов в папке
    return render_template('filetable.html', files=allowed_files)


@app.route('/upload', methods=['GET', 'POST'])  #страница загрузки
@check
def upload():
    user_name = session.get('user_id')
    if request.method == 'POST':
        if 'file' not in request.files:
            abort(400, "Нет файла")
        file = request.files['file']
        filename = file.filename
        if filename:
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            owners.fil_owner(filename, user_name)
            return redirect(url_for('divide_files'))

    # GET-запрос или при ошибке — показываем страницу загрузки
    return render_template('upload.html')

@app.route('/login', methods=['GET', 'POST']) #страница логина
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if valid_login(username, password):
            session['user_id'] = username  # присваиваем в сессию
            return log_the_user_in()
        else:
            error = 'Invalid username/password'
        # Для GET-запроса или при ошибке — отображается форма логина
    return render_template('login.html', error=error)

@app.route('/logout') #выход
def logout():
    session.clear()  # удаляем все данные о сессии
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='192.168.0.106', port=9056,debug=True)
