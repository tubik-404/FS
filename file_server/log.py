import sqlite3

conn = sqlite3.connect('static/login.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS login(
    id INTEGER PRIMARY KEY,
    name text not null,
    pass text not null
)
''')
conn.commit()
conn.close()

def inp(n, p):
    conn = sqlite3.connect('static/login.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO login (name, pass) VALUES (?,?)', (n, p))
    conn.commit()
    conn.close()

def prt():
    conn = sqlite3.connect('static/login.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM login')
    for i in cursor.fetchall():
        print(i)
    conn.close()

def log_n(username):
    conn = sqlite3.connect('static/login.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM login WHERE name = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None


def log_p(pas):
    conn = sqlite3.connect('static/login.db')
    cursor = conn.cursor()
    cursor.execute('SELECT pass FROM login WHERE pass = ?', (pas,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def check_name(n):
    conn = sqlite3.connect('static/login.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM login WHERE name = ?', (n,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

#inp('admin', 'admin')
#prt()
#check_name('dak')