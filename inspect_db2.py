import sqlite3

conn = sqlite3.connect(r'C:\Users\Dell\map_project\google_maps_leads\db.sqlite3')
cursor = conn.cursor()

# Check leads_lead table
cursor.execute("PRAGMA table_info('leads_lead')")
cols = cursor.fetchall()
print('leads_lead columns:')
for col in cols:
    print(f'  {col}')

cursor.execute("SELECT COUNT(*) FROM leads_lead")
count = cursor.fetchone()[0]
print(f'Row count: {count}')

cursor.execute("SELECT * FROM leads_lead LIMIT 5")
rows = cursor.fetchall()
print('Sample rows:')
for row in rows:
    # Convert to safe string
    safe_row = []
    for item in row:
        if isinstance(item, str):
            safe_row.append(item.encode('ascii', 'ignore').decode('ascii'))
        else:
            safe_row.append(item)
    print(f'  {safe_row}')

# Check leads_emaillead table
print('\n\nleads_emaillead columns:')
cursor.execute("PRAGMA table_info('leads_emaillead')")
cols = cursor.fetchall()
for col in cols:
    print(f'  {col}')

cursor.execute("SELECT COUNT(*) FROM leads_emaillead")
count = cursor.fetchone()[0]
print(f'Row count: {count}')

cursor.execute("SELECT * FROM leads_emaillead LIMIT 5")
rows = cursor.fetchall()
print('Sample rows:')
for row in rows:
    safe_row = []
    for item in row:
        if isinstance(item, str):
            safe_row.append(item.encode('ascii', 'ignore').decode('ascii'))
        else:
            safe_row.append(item)
    print(f'  {safe_row}')

# Check unique emails and statuses in leads_lead
print('\n\nUnique emails in leads_lead:')
cursor.execute("SELECT DISTINCT email FROM leads_lead WHERE email IS NOT NULL AND email != ''")
emails = cursor.fetchall()
for e in emails:
    print(f'  {e[0]}')

print('\nUnique statuses in leads_lead:')
cursor.execute("SELECT DISTINCT status FROM leads_lead WHERE status IS NOT NULL")
statuses = cursor.fetchall()
for s in statuses:
    print(f'  {s[0]}')

# Check unique emails and statuses in leads_emaillead
print('\n\nUnique emails in leads_emaillead:')
cursor.execute("SELECT DISTINCT email FROM leads_emaillead WHERE email IS NOT NULL AND email != ''")
emails = cursor.fetchall()
for e in emails:
    print(f'  {e[0]}')

print('\nUnique statuses in leads_emaillead:')
cursor.execute("SELECT DISTINCT status FROM leads_emaillead WHERE status IS NOT NULL")
statuses = cursor.fetchall()
for s in statuses:
    print(f'  {s[0]}')

conn.close()