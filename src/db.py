import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Runs table: tracks each execution of the pipeline
    c.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            total_fetched INTEGER,
            novel_found INTEGER,
            high_signal_found INTEGER,
            status TEXT
        )
    ''')
    # Articles table: tracks articles processed in a run
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            title TEXT,
            link TEXT,
            score INTEGER,
            reasoning TEXT,
            status TEXT
        )
    ''')
    # Posts table: tracks generated posts
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            article_title TEXT,
            draft_content TEXT,
            ai_editor_passed BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def create_run():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO runs (timestamp, total_fetched, novel_found, high_signal_found, status) VALUES (?, 0, 0, 0, 'RUNNING')", (timestamp,))
    run_id = c.lastrowid
    conn.commit()
    conn.close()
    return run_id

def update_run_stats(run_id, total_fetched, novel_found, high_signal_found, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE runs 
        SET total_fetched=?, novel_found=?, high_signal_found=?, status=?
        WHERE id=?
    ''', (total_fetched, novel_found, high_signal_found, status, run_id))
    conn.commit()
    conn.close()

def log_article(run_id, title, link, score, reasoning, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO articles (run_id, title, link, score, reasoning, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (run_id, title, link, score, reasoning, status))
    conn.commit()
    conn.close()
    
def log_post(run_id, article_title, draft_content, ai_editor_passed):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO posts (run_id, article_title, draft_content, ai_editor_passed)
        VALUES (?, ?, ?, ?)
    ''', (run_id, article_title, draft_content, ai_editor_passed))
    conn.commit()
    conn.close()
