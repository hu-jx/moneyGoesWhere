import sqlite3
from datetime import datetime
db = "bot_data.db"

def init_db():
    """
    Create a new database for expenses record of user
    """
    with sqlite3.connect(db) as conn:
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
        cursor.execute(""" SELECT SUM(cost)
                    FROM expenses
                    WHERE user_id = ? AND 
                            strftime('%Y-%m', timestamp) = strftime('%Y-%m', ?)""",
                    (user_id, date))
        total = cursor.fetchone()[0]
    return total or 0 

def reset() -> None:
    """
    Clears the SQLite database to return an empty table of records
    """
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS expenses")
        
        conn.commit()

def todays_records(user_id: int, date:datetime) -> list:
    """
    Returns all expenses records corresponding to today's date
    """
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT * 
                       FROM expenses 
                       WHERE user_id = ? AND 
                            DATE(timestamp) =  DATE(?)
                       """, (user_id, date))
        table = cursor.fetchall()
    return table

def get_monthly(user_id: int, date: datetime) -> list:
    """
    Returns all expenses record for the current month
    """
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT * 
                       FROM expenses 
                       WHERE user_id = ? AND 
                            strftime('%Y-%m', timestamp) = strftime('%Y-%m', ?)
                       """, (user_id, date))
        table = cursor.fetchall()
    return table

def update_record(user_id: int, record_id: int, field: str, val: str):
    if not check_if_exist(record_id, user_id):
        raise Exception("Record does not exist or you do not have permissions to delete it.")
    ##Column check 
    columns = ['date', 'category', 'cost', 'cat']
    if field not in columns:
        raise ValueError(f"Invalid or unauthorized column name: {field}")
    
    #Value checks for field and corresponding values 
    if field == 'date': ##separate into different classes extending the same thing 
        val = datetime.fromisoformat(val)
        field = 'timestamp'
        with sqlite3.connect(db) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""UPDATE expenses 
                        SET {field} = DATETIME(?)
                        WHERE id = ? AND user_id = ?""", (val, record_id, user_id))
            conn.commit()
        return
        
    elif field in ['cat', 'category']:
        field = 'category'
    elif field == 'cost':
        val = float(val)
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""UPDATE expenses 
                    SET {field} = ?
                    WHERE id = ? AND user_id = ?""", (val, record_id, user_id))
        conn.commit()

def delete(user_id, record_id):
    if not check_if_exist(record_id, user_id):
        raise Exception("Record does not exist or you do not have permission to delete it.")
    
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""DELETE FROM expenses 
                       WHERE id = ? AND user_id = ?""", (record_id, user_id))
        conn.commit()

def check_if_exist(record_id, user_id):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT 1 FROM expenses 
                          WHERE id = ? AND user_id = ? 
                          LIMIT 1""", (record_id, user_id))
        return cursor.fetchone() is not None
