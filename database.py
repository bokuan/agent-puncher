import sqlite3
import json
from datetime import datetime

# Initialize the database
def init_db():
    conn = sqlite3.connect('llm_gateway.db')
    cursor = conn.cursor()
    
    # Create logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        prompt TEXT NOT NULL,
        response TEXT NOT NULL,
        tokens_used INTEGER,
        external_api_url TEXT NOT NULL,
        request_headers TEXT,
        request_body TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Insert a new log entry
def insert_log(prompt, response, tokens_used, external_api_url, request_headers, request_body):
    conn = sqlite3.connect('llm_gateway.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute('''
    INSERT INTO logs (timestamp, prompt, response, tokens_used, external_api_url, request_headers, request_body)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, prompt, response, tokens_used, external_api_url, json.dumps(request_headers), json.dumps(request_body)))
    
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id

# Get all logs
def get_logs():
    conn = sqlite3.connect('llm_gateway.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC')
    logs = cursor.fetchall()
    
    conn.close()
    return logs

# Update an existing log entry
def update_log(log_id, response, tokens_used):
    conn = sqlite3.connect('llm_gateway.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE logs 
    SET response = ?, tokens_used = ? 
    WHERE id = ?
    ''', (response, tokens_used, log_id))
    
    conn.commit()
    conn.close()
