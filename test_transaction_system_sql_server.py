import pyodbc
import unittest

# Database setup
class DatabaseConnection:
    def __init__(self, server, database, username, password):
        self.connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    def __enter__(self):
        self.connection = pyodbc.connect(self.connection_string)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def create_tables(self):
        with self.connection.cursor() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY IDENTITY,
                username NVARCHAR(100) NOT NULL,
                role NVARCHAR(50) NOT NULL
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INT PRIMARY KEY IDENTITY,
                transaction_type NVARCHAR(100) NOT NULL,
                status NVARCHAR(50) NOT NULL,
                notes NVARCHAR(MAX)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS audit_trail (
                id INT PRIMARY KEY IDENTITY,
                username NVARCHAR(100) NOT NULL,
                action NVARCHAR(100) NOT NULL,
                transaction_id INT,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id)
            )''')
            self.connection.commit()

# Roles and Users
class Role:
    MAKER = 'Maker'
    CHECKER = 'Checker'
    ADMIN = 'Admin'

class User:
    def __init__(self, username, role):
        self.username = username
        self.role = role

class Transaction:
    def __init__(self, transaction_id, transaction_type):
        self.transaction_id = transaction_id
        self.transaction_type = transaction_type
        self.status = 'Pending'
        self.notes = []

    def add_notes(self, note):
        self.notes.append(note)

# Manager Classes
class TransactionManager:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def create_transaction(self, transaction):
        with self.db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (transaction_type, status, notes) VALUES (?, ?, ?)",
                           (transaction.transaction_type, transaction.status, ''))
            conn.commit()

    def get_transactions(self, status=None):
        with self.db_connection as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM transactions WHERE status=?", (status,))
            else:
                cursor.execute("SELECT * FROM transactions")
            transactions = cursor.fetchall()
            return [Transaction(transaction[0], transaction[1]) for transaction in transactions]

    def update_transaction_status(self, transaction_id, status):
        with self.db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE transactions SET status=? WHERE id=?", (status, transaction_id))
            conn.commit()

class AuditTrail:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def log_action(self, user, action, transaction_id):
        with self.db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO audit_trail (username, action, transaction_id) VALUES (?, ?, ?)",
                           (user.username, action, transaction_id))
            conn.commit()

class NotesManager:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def add_note_to_transaction(self, transaction_id, note):
        with self.db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE transactions SET notes = notes + ? WHERE id=?", (f"\n{note}", transaction_id))
            conn.commit()

# Tests
class TestTransactionSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_connection = DatabaseConnection('your_server', 'your_database', 'your_username', 'your_password')
        cls.transaction_manager = TransactionManager(cls.db_connection)
        cls.audit_trail = AuditTrail(cls.db_connection)
        cls.notes_manager = NotesManager(cls.db_connection)
        cls.maker = User('maker_user', Role.MAKER)
        cls.checker = User('checker_user', Role.CHECKER)

        cls.db_connection.__enter__().cursor().execute('''DELETE FROM transactions; DELETE FROM audit_trail;''')
        cls.db_connection.create_tables()

    def setUp(self):
        # Clear previous entries
        with self.db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM audit_trail")
            conn.commit()

    def test_audit_trail(self):
        transaction = Transaction(1, 'Subscription')
        self.transaction_manager.create_transaction(transaction)
        self.audit_trail.log_action(self.maker, 'Created Transaction', transaction.transaction_id)

        with self.db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_trail WHERE username=?", (self.maker.username,))
            logs = cursor.fetchall()
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0][2], 'Created Transaction')

    def test_add_notes(self):
        transaction = Transaction(2, 'Redemption')
        self.transaction_manager.create_transaction(transaction)
        self.notes_manager.add_note_to_transaction(transaction.transaction_id, 'Initial note by maker')
        self.notes_manager.add_note_to_transaction(transaction.transaction_id, 'Approval note by checker')

        with self.db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT notes FROM transactions WHERE id=?", (transaction.transaction_id,))
            notes = cursor.fetchone()[0]
        
        self.assertIn('Initial note by maker', notes)
        self.assertIn('Approval note by checker', notes)

    def test_filter_transactions_by_user(self):
        transaction1 = Transaction(3, 'Switching')
        transaction2 = Transaction(4, 'Subscription')
        self.transaction_manager.create_transaction(transaction1)
        self.transaction_manager.create_transaction(transaction2)

        pending_transactions = self.transaction_manager.get_transactions(status='Pending')

        self.assertEqual(len(pending_transactions), 2)
        self.assertEqual(pending_transactions[0].transaction_id, transaction1.transaction_id)
        self.assertEqual(pending_transactions[1].transaction_id, transaction2.transaction_id)

if __name__ == '__main__':
    unittest.main()
