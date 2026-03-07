import sqlite3

conn = sqlite3.connect('static/owners.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS owners(
    id INTEGER PRIMARY KEY,
    file text not null,
    name text not null
)
''')
conn.close()

def inp(file, name):
    conn = sqlite3.connect('static/owners.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO owners (file, name) VALUES (?,?)', (file, name))
    conn.close()

def prt():
    conn = sqlite3.connect('static/owners.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM owners')
    for i in cursor.fetchall():
        print(i)
    conn.close()

def sel_f(user_name):
    conn = sqlite3.connect('static/owners.db')
    cursor = conn.cursor()
    cursor.execute('SELECT file FROM owners where name = ?', (user_name,))
    res = cursor.fetchall()
    return [res[0] for res in res]

def fil_owner(filename,user_name):
    conn = sqlite3.connect('static/owners.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO owners (file, name) VALUES(?,?)', (filename, user_name))
    conn.commit()

def clear_owner(fil):
    conn = sqlite3.connect('static/owners.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM owners WHERE file=?', (fil,))
    conn.commit()

#inp('уязвимость.PNG','kit')
#prt()
#sel_f()
#clear_owner()