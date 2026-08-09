import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cursor = conn.cursor()

print("Schema of peer_groups:")
for r in cursor.execute("PRAGMA table_info(peer_groups)").fetchall():
    print(r)

print("\nSample rows in peer_groups:")
for r in cursor.execute("SELECT * FROM peer_groups LIMIT 10").fetchall():
    print(r)

conn.close()
