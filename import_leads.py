#!/usr/bin/env python
"""
Import leads from C:\\Users\\Dell\\map_project\\google_maps_leads\\db.sqlite3
into LocalLeadsProject leads.db, comparing by email and status to avoid duplicates.
"""
import sqlite3
import os
import sys
from datetime import datetime

SOURCE_DB = r"C:\\Users\\Dell\\map_project\\google_maps_leads\\db.sqlite3"
TARGET_DB = r"D:\\ComsysProject\\output\\LocalLeadsProject\\leads.db"

def get_source_leads():
    """Extract leads from source database, parsing comma-separated emails."""
    conn = sqlite3.connect(SOURCE_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, phone, website, address, email, category, 
               review_count, avg_rating, lat, lng, raw_json,
               created_at, updated_at, email_status, status
        FROM leads_lead
        WHERE email IS NOT NULL AND email != ''
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    leads = []
    for row in rows:
        (lead_id, name, phone, website, address, email, category,
         review_count, avg_rating, lat, lng, raw_json,
         created_at, updated_at, email_status, status) = row
        
        # Parse comma-separated emails
        emails = [e.strip() for e in email.split(',') if e.strip()]
        
        for single_email in emails:
            leads.append({
                'source_id': lead_id,
                'name': name,
                'phone': phone,
                'website': website,
                'address': address,
                'email': single_email,
                'company': category,
                'position': '',
                'source': 'google_maps',
                'status': status or 'pending',
                'score': 0,
                'notes': f'Imported from Google Maps. Category: {category}. Reviews: {review_count}. Rating: {avg_rating}. Location: {lat},{lng}',
                'created_at': created_at,
                'updated_at': updated_at,
                'last_contacted': None,
                'next_followup': None,
                'email_status': email_status
            })
    
    return leads

def get_target_emails():
    """Get all emails from target database for duplicate checking."""
    conn = sqlite3.connect(TARGET_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT email, status FROM leads WHERE email IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    
    # Return set of (email_lower, status) tuples for comparison
    return {(email.lower().strip(), status) for email, status in rows}

def import_leads():
    """Import leads from source to target, skipping duplicates."""
    print(f"Reading source database: {SOURCE_DB}")
    source_leads = get_source_leads()
    print(f"Found {len(source_leads)} lead emails (after parsing comma-separated)")
    
    print(f"Reading target database: {TARGET_DB}")
    target_emails = get_target_emails()
    print(f"Target has {len(target_emails)} existing email+status combinations")
    
    # Connect to target for insertion
    conn = sqlite3.connect(TARGET_DB)
    cursor = conn.cursor()
    
    imported = 0
    skipped = 0
    duplicates_detail = []
    
    for lead in source_leads:
        email_key = (lead['email'].lower().strip(), lead['status'])
        
        if email_key in target_emails:
            skipped += 1
            duplicates_detail.append(f"  Skipped duplicate: {lead['email']} ({lead['status']}) - {lead['name'][:50]}")
            continue
        
        # Insert new lead
        cursor.execute("""
            INSERT INTO leads (name, email, phone, company, position, source, status, score, notes,
                              created_at, updated_at, last_contacted, next_followup)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead['name'],
            lead['email'],
            lead['phone'],
            lead['company'],
            lead['position'],
            lead['source'],
            lead['status'],
            lead['score'],
            lead['notes'],
            lead['created_at'],
            lead['updated_at'],
            lead['last_contacted'],
            lead['next_followup']
        ))
        
        imported += 1
        target_emails.add(email_key)  # Update set to catch duplicates within source
        
        if imported % 20 == 0:
            print(f"  Imported {imported} leads...")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Import Summary ===")
    print(f"Total source lead emails: {len(source_leads)}")
    print(f"Imported: {imported}")
    print(f"Skipped (duplicates): {skipped}")
    
    if duplicates_detail:
        print(f"\nDuplicate details:")
        for d in duplicates_detail[:20]:  # Show first 20
            print(d)
        if len(duplicates_detail) > 20:
            print(f"  ... and {len(duplicates_detail) - 20} more")

def show_target_stats():
    """Show statistics of target database after import."""
    conn = sqlite3.connect(TARGET_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
    status_counts = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(DISTINCT email) FROM leads WHERE email IS NOT NULL")
    unique_emails = cursor.fetchone()[0]
    
    print(f"\n=== Target Database Stats ===")
    print(f"Total leads: {total}")
    print(f"Unique emails: {unique_emails}")
    print(f"Status breakdown:")
    for status, count in status_counts:
        print(f"  {status}: {count}")
    
    conn.close()

if __name__ == "__main__":
    if not os.path.exists(SOURCE_DB):
        print(f"Source database not found: {SOURCE_DB}")
        sys.exit(1)
    
    if not os.path.exists(TARGET_DB):
        print(f"Target database not found: {TARGET_DB}")
        print("Run the LocalLeadsProject app first to create the database.")
        sys.exit(1)
    
    import_leads()
    show_target_stats()