from flask import Flask, session, send_from_directory, request, abort, render_template, redirect, url_for, send_file
import os, logging, owners, log, random, string, secrets
from functools import wraps
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_SECURE=True,    # Куки передаются только по HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Куки недоступны для JavaScript (защита от XSS)
    SESSION_COOKIE_SAMESITE='Lax', # Защита от CSRF
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'files')  # папка, где хранятся файлы
app.secret_key = os.environ.get('New_encrypted_secret_key_value', secrets.token_hex(32))
tech_dir = os.path.dirname(os.path.abspath(__file__))

@app.after_request
def add_security_headers(response):
    # 2. Content Security Policy (CSP): разрешаем ресурсы только с нашего домена
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline';"
    # 3. Clickjacking Protection: запрещаем отображение сайта в iframe
    response.headers['X-Frame-Options'] = 'DENY'
    # 4. MIME Type Confusion: запрещаем браузеру угадывать тип контента
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Дополнительная защита от XSS для старых браузеров
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.before_request
def before_request():
    if not request.is_secure and app.env != 'development':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

log_path = os.path.join(tech_dir, 'app.log')  #логирование
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def valid_login(username, password): #логика авторизации
    storedname = log.log_n(username)
    storedpass = log.log_p(password)

    if (username == storedname):
        if (password == storedpass):
            return True
        else:
            return False
    else:
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
    1/0

@app.route('/')#Главная страница
@check
def home():
    user_name = session.get('user_id')
    return render_template('index.html', username=user_name)


@app.route('/download/<filename>')
@check
def download_file(filename):
    user_name = session.get('user_id')

    allowed_files = owners.sel_f(user_name)

    if filename not in allowed_files:
        logging.warning(f"IDOR ATTEMPT: User {user_name} tried to access {filename}")
        return abort(403)

    logging.info(f"{request.remote_addr} User: {user_name}, download {filename}")
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/files')#страница просмотра файлов
@check
def divide_files():
    user_name = session.get('user_id')
    allowed_files = owners.sel_f(user_name)
    return render_template('filetable.html', files=allowed_files)

@app.route('/upload', methods=['GET', 'POST'])  #страница загрузки
@check
def upload():
    user_name = session.get('user_id')
    if request.method == 'POST':
        if 'file' not in request.files:
            abort(400, "Нет файла")
        file = request.files['file']
        filename = secure_filename(file.filename)
        if filename:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            owners.fil_owner(filename, user_name)
            return redirect(url_for('divide_files'))
    return render_template('upload.html')

@app.route('/login', methods=['GET', 'POST']) #страница логина
def login():
    error = None
    if request.method == 'POST':
        user_input = request.form.get('captcha_input', '').strip().upper()
        real_text = session.pop('captcha_text', '').upper()
        username = request.form['username']
        password = request.form['password']
        logging.info(f"Login attempt for user: {username} from IP: {request.remote_addr}")

        if not real_text or user_input != real_text:
            error = 'Капча неверна или устарела. Обновите страницу.'
            logging.warning(f"Invalid captcha attempt for: {username}")
            return render_template('login.html', error=error)

        if valid_login(username, password):
            if(user_input==real_text):
                session['user_id'] = username
                return log_the_user_in()
            else:
                error = 'Неверно введенная капча'
                logging.warning(f"Failed kaptcha for user: {username} from IP: {request.remote_addr}")
        else:
            error = 'Неверное имя пользователя или пароль'
            logging.warning(f"Failed login for user: {username} from IP: {request.remote_addr}")
    return render_template('login.html', error=error)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    error = None
    if request.method == 'POST':
        user_input = request.form.get('captcha_input', '').strip().upper()
        real_text = session.get('captcha_text', '').upper()
        username = request.form['username']
        password = request.form['password']
        password_check = request.form['password-check']

        if(password == password_check and username != "" and password != ""):
            if(log.check_name(username) == None):
                if(user_input==real_text):
                    log.inp(username, password)
                    session['user_id'] = username
                    return log_the_user_in()
                else:
                    error = 'Неверно введенная капча'
            else:
                error = 'Имя занято'
                return render_template('registration.html', error=error)
        else:
            error='Пароли не совпадают'
            return render_template('registration.html', error=error)
    return render_template('registration.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/delete/<filename>')
@check
def delete_file(filename):
    user_name = session.get('user_id')
    logging.info(f"{request.remote_addr} User: {user_name}, delete {filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
        owners.clear_owner(filename)
        return redirect(url_for('divide_files'))
    else:
        return redirect(url_for('divide_files'))

#капча
def generate_captcha_text(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_captcha_image(text):
    width, height = 150, 40
    image = Image.new('RGB', (width, height), (255, 255, 255))
    font = ImageFont.load_default()  # Можно указать свой шрифт
    draw = ImageDraw.Draw(image)

    for _ in range(10):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=(0, 0, 0), width=1)

    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width)//2
    text_y = (height - text_height)//2
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    return image

@app.route('/captcha')
def captcha():
    captcha_text = generate_captcha_text()
    session['captcha_text'] = captcha_text
    image = create_captcha_image(captcha_text)
    buf = BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='192.168.0.106', port=9056,debug=True, ssl_context='adhoc')

#192.168.0.106
#fe80::a5e4:a580:e650:3da0%8