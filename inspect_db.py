import sqlite3

conn = sqlite3.connect(r'C:\Users\Dell\map_project\google_maps_leads\db.sqlite3')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

for table in tables:
    cursor.execute(f'PRAGMA table_info({table[0]})')
    cols = cursor.fetchall()
    print(f'\n{table[0]} columns:')
    for col in cols:
        print(f'  {col}')
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    count = cursor.fetchone()[0]
    print(f'  Row count: {count}')

    # Show sample data
    cursor.execute(f'SELECT * FROM {table[0]} LIMIT 3')
    rows = cursor.fetchall()
    print(f'  Sample rows:')
    for row in rows:
        print(f'    {row}')

conn.close()