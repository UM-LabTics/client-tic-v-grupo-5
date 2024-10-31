import sqlite3

connection = sqlite3.connect("people.db")

cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS people(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	document_id TEXT UNIQUE NOT NULL,
    photo TEXT NOT NULL,
    encoding BLOB NOT NULL
)
''')

connection.commit()

connection.close()
