import sqlite3
import datetime

db = "bot_data.db"

def init_db():
    """
    Create a new database for expenses record of user
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL, 
                   category TEXT, 
                   cost DECIMAL,
                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                   )
                   """)
    conn.commit()
    cursor.close()
    conn.close()


def add_expense(user_id: int, timestamp: datetime, cat : str, cost: float) -> None:
    """
    Updates database with a new record of expense 
    """
    with sqlite3.connect(db) as conn:
        conn.execute("""INSERT INTO expenses (user_id, category, cost, timestamp)
                     VALUES (?, ?, ?, ?)""",
                     (user_id, cat, cost, timestamp))
        conn.commit()

def filter_daily(user_id: int, date:datetime) -> float:
    """
    Filters database to return total for the current date
    """
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(""" SELECT SUM(cost)
                    FROM expenses
                    WHERE user_id = ? AND DATE(timestamp) =  DATE(?)""", 
                    (user_id, date))
        total = cursor.fetchone()[0]
    return total or 0 

def filter_monthly(user_id: int, date: datetime) -> float:
    """
    Filters database to return the sum of expenses for the current month
    """
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(f""" SELECT SUM(cost)
                    FROM expenses
                    WHERE user_id = ? AND 
                            strftime('%Y-%m', timestamp) = strftime('%Y-%m', ?)""",
                    (user_id, date))
        total = cursor.fetchone()[0]
    return total or 0 
