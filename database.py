import sqlite3
import hashlib

class DatabaseManager:
    def __init__(self, db_name="gastos.db"):
        self.db_name = db_name
        self.init_db()

    def run_query(self, query, parameters=()):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            result = cursor.execute(query, parameters)
            conn.commit()
        return result

    def init_db(self):
        self.run_query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        self.run_query("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        """)

        try:
            hashed_pw = hashlib.sha256("password123".encode()).hexdigest()
            self.run_query("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hashed_pw))
        except sqlite3.IntegrityError:
            pass # El usuario ya existe

        self.populate_dummy_data()

    def populate_dummy_data(self):
        # Verificar si hay gastos
        cursor = self.run_query("SELECT count(*) FROM expenses")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Base de datos vacía. Insertando datos simulados...")
            dummy_data = [
                ("Alimentación", 1500.50, "Supermercado Semanal"),
                ("Transporte", 200.00, "Gasolina"),
                ("Ocio", 450.00, "Cine y Cena"),
                ("Servicios", 800.00, "Pago de Internet y Luz"),
                ("Alimentación", 120.00, "Desayuno trabajo"),
                ("Salud", 600.00, "Farmacia y medicinas"),
                ("Transporte", 50.00, "Uber"),
                ("Otros", 300.00, "Regalo de cumpleaños")
            ]
            
            for cat, amount, desc in dummy_data:
                self.add_expense(cat, amount, desc)

    def validate_login(self, username, password):
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        result = self.run_query("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
        return result.fetchone() is not None

    # --- CRUD ---
    def add_expense(self, category, amount, description):
        self.run_query("INSERT INTO expenses (category, amount, description) VALUES (?, ?, ?)", 
                       (category, amount, description))

    def get_expenses(self):
        cursor = self.run_query("SELECT * FROM expenses ORDER BY id DESC")
        return cursor.fetchall()

    def delete_expense(self, expense_id):
        self.run_query("DELETE FROM expenses WHERE id = ?", (expense_id,))

    def update_expense(self, id, category, amount, description):
        self.run_query("UPDATE expenses SET category=?, amount=?, description=? WHERE id=?",
                       (category, amount, description, id))

    def get_expenses_by_category(self):
        cursor = self.run_query("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        return cursor.fetchall()