
import sqlite3
from datetime import datetime

DB_PATH = 'records.db'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_records (
            steam_id TEXT PRIMARY KEY,
            best_kda REAL DEFAULT 0,
            last_updated TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_records(steam_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT best_kda, last_updated FROM player_records WHERE steam_id = ?', (steam_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {'best_kda': row[0], 'last_updated': row[1]}
    return None


def update_records(steam_id: str, current_kda: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT best_kda FROM player_records WHERE steam_id = ?', (steam_id,))
    row = cursor.fetchone()

    new_records = False

    if row:
        current_best_kda = row[0]
        if current_kda > current_best_kda:
            new_records = True
            cursor.execute('''
                UPDATE player_records 
                SET best_kda = ?, last_updated = ?
                WHERE steam_id = ?
            ''', (current_kda, datetime.now().isoformat(), steam_id))
    else:
        new_records = True
        cursor.execute('''
            INSERT INTO player_records (steam_id, best_kda, last_updated)
            VALUES (?, ?, ?)
        ''', (steam_id, current_kda, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return new_records


def format_records_message(steam_id: str, current_kda: float):
    records = get_records(steam_id)

    if not records:
        return "Личный рекорд KDA:пока нет данных"

    message = f"Личный рекорд KDA: {records['best_kda']:.2f}\n"
    message += f"Установлен: {records['last_updated'][:10]}"

    if current_kda > records['best_kda']:
        message += f"\n\n🎉 **НОВЫЙ РЕКОРД KDA: {current_kda:.2f} (было {records['best_kda']:.2f})"

    return message