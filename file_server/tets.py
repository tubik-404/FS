from flask import Flask, session, render_template_string, request, send_file
from io import BytesIO
import random
import string
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # замените на ваш секретный ключ

# Рендер HTML
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Python капча</title>
</head>
<body>
<h2>Введите код с картинки</h2>
{% if message %}
<p style="color: red;">{{ message }}</p>
{% endif %}
<form method="post">
    <p>
        <img src="{{ url_for('captcha') }}" alt="Капча"/><br/>
        <input type="text" name="captcha_input" required />
    </p>
    <button type="submit">Отправить</button>
</form>
</body>
</html>
'''


# Генерируем случайный текст капчи
def generate_captcha_text(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# Создаем изображение капчи
def create_captcha_image(text):
    width, height = 200, 70
    image = Image.new('RGB', (width, height), (255, 255, 255))
    font = ImageFont.load_default()  # Можно указать свой шрифт
    draw = ImageDraw.Draw(image)

    # Добавляем шум или линию (по желанию)
    for _ in range(10):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=(0, 0, 0), width=1)

    # Накладываем текст
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width)//2
    text_y = (height - text_height)//2
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    # Можно добавить искажения или шум
    return image


@app.route('/captcha')
def captcha():
    captcha_text = session.get('captcha_text')
    if not captcha_text:
        captcha_text = generate_captcha_text()
        session['captcha_text'] = captcha_text
    image = create_captcha_image(captcha_text)
    buf = BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        user_input = request.form.get('captcha_input', '').strip().upper()
        real_text = session.get('captcha_text', '').upper()
        if user_input == real_text:
            message = 'Код верный!'
        else:
            message = 'Неверный код!'
        # Генерируем новую капчу после проверки
        session.pop('captcha_text', None)
    return render_template_string(HTML_TEMPLATE, message=message)


if __name__ == '__main__':
    app.run(debug=True)