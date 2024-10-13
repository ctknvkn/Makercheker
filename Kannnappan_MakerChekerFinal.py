import logging
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import unittest

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URI = (
    'mssql+pyodbc://DSQLDMFO/DM_FrontOffice?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server'
)

# Create an engine and base class
engine = create_engine(DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Model Definitions
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    notes = Column(String, nullable=True)

class AuditTrail(Base):
    __tablename__ = 'audit_trail'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))

# Create tables
Base.metadata.create_all(engine)

# Helper function to log actions
def log_action(username, action, transaction_id=None):
    session = Session()
    try:
        audit_entry = AuditTrail(username=username, action=action, transaction_id=transaction_id)
        session.add(audit_entry)
        session.commit()
    finally:
        session.close()

# Manager Classes
class TransactionManager:
    def create_transaction(self, username, transaction_type, status):
        session = Session()
        try:
            transaction = Transaction(transaction_type=transaction_type, status=status)
            session.add(transaction)
            session.commit()
            log_action(username, f"Created {transaction_type} transaction", transaction.id)
            return transaction.id
        finally:
            session.close()

    def edit_transaction(self, username, transaction_id, transaction_type, status):
        session = Session()
        try:
            transaction = session.query(Transaction).get(transaction_id)
            if transaction and transaction.status == 'Pending':
                transaction.transaction_type = transaction_type
                transaction.status = status
                session.commit()
                log_action(username, f"Edited transaction {transaction_id}", transaction_id)
        finally:
            session.close()

    def cancel_transaction(self, username, transaction_id):
        session = Session()
        try:
            transaction = session.query(Transaction).get(transaction_id)
            if transaction and transaction.status == 'Pending':
                transaction.status = 'Cancelled'
                session.commit()
                log_action(username, f"Cancelled transaction {transaction_id}", transaction_id)
        finally:
            session.close()

    def approve_transaction(self, username, transaction_id):
        session = Session()
        try:
            transaction = session.query(Transaction).get(transaction_id)
            if transaction and transaction.status == 'Pending':
                transaction.status = 'Approved'
                session.commit()
                log_action(username, f"Approved transaction {transaction_id}", transaction_id)
        finally:
            session.close()

    def reject_transaction(self, username, transaction_id):
        session = Session()
        try:
            transaction = session.query(Transaction).get(transaction_id)
            if transaction and transaction.status == 'Pending':
                transaction.status = 'Rejected'
                session.commit()
                log_action(username, f"Rejected transaction {transaction_id}", transaction_id)
        finally:
            session.close()

    def get_transactions(self, username, status=None):
        session = Session()
        try:
            query = session.query(Transaction)
            if status:
                query = query.filter_by(status=status)
            transactions = query.all()
            log_action(username, "Viewed transactions")
            return transactions
        finally:
            session.close()

class NotesManager:
    def add_note_to_transaction(self, username, transaction_id, note):
        session = Session()
        try:
            transaction = session.query(Transaction).get(transaction_id)
            if transaction:
                transaction.notes = (transaction.notes or '') + f"{note}\n"
                session.commit()
                log_action(username, f"Added note to transaction {transaction_id}", transaction_id)
        finally:
            session.close()

class AdminManager:
    def create_user(self, session,username, new_username, role):
        #session = Session()
        try:
            user = User(username=new_username, role=role)
            session.add(user)
            log_action(username, f"Create user {new_username}")
            

            session.commit()
            log_action(username, f"Created user {new_username}")
        except SQLAlchemyError as e:
            log_action(username, f"Error creating user: {e}")
            logger.error(f"Error creating user: {e}")
            session.rollback()

    def edit_user(self, session,username, user_id, new_role):
        #session = Session()
        try:
            user = session.query(User).get(user_id)
            if user:
                logger.debug(f"User found: {user.username} with current role: {user.role}")
                user.role = new_role
                session.commit()
                log_action(username, f"Edited user {user_id} to role {new_role}")
                logger.debug(f"User role updated to: {user.role}")
            else:
                logger.debug(f"User with ID {user_id} not found")
        except SQLAlchemyError as e:
            logger.error(f"Error updating user: {e}")
       
    def delete_user(self, username, user_id):
        session = Session()
        try:
            user = session.query(User).get(user_id)
            if user:
                session.delete(user)
                session.commit()
                log_action(username, f"Deleted user {user_id}")
        finally:
            session.close()

# Tests
class TestTransactionSystem(unittest.TestCase):
    def setUp(self):
        session = Session()
        try:
            # Clear previous entries
            session.query(AuditTrail).delete()
            session.query(Transaction).delete()
            session.query(User).delete()
            session.commit()

            # Add users
            session.add_all([
                User(username='maker_user', role='Maker'),
                User(username='checker_user', role='Checker'),
                User(username='admin_user', role='Admin')
            ])
            session.commit()
        finally:
            session.close()

    def test_transaction_workflow(self):
        manager = TransactionManager()
        notes_manager = NotesManager()
        admin_manager = AdminManager()

        # Maker creates a transaction
        transaction_id = manager.create_transaction('maker_user', 'Subscription', 'Pending')

        # Maker edits the transaction
        manager.edit_transaction('maker_user', transaction_id, 'Redemption', 'Pending')

        # Maker adds notes
        notes_manager.add_note_to_transaction('maker_user', transaction_id, 'Initial note by maker')

        # Checker approves the transaction
        manager.approve_transaction('checker_user', transaction_id)

        # Verify notes
        session = Session()
        try:
            transaction = session.get(Transaction, transaction_id)
            self.assertIn('Initial note by maker', transaction.notes)
            self.assertEqual(transaction.status, 'Approved')
        finally:
            session.close()

    def test_admin_features(self):

        admin_manager = AdminManager()
        session = Session()
        # Admin creates a new user
        admin_manager.create_user(session,'admin_user', 'new_makeruser', 'Maker')

        session.commit()
        try:
            # Retrieve the newly created user
            new_user = session.query(User).filter_by(username='new_makeruser').first()
            self.assertIsNotNone(new_user, "User should be created")

            # Verify user name and role
            new_user = session.query(User).get(new_user.id)
            self.assertEqual(new_user.username, 'new_makeruser')
            #Admin edits the user role
            admin_manager.edit_user(session,'admin_user', new_user.id, 'Checker')
            session.commit()
            # Verify user role
            updated_user = session.query(User).get(new_user.id)
            self.assertEqual(updated_user.role, 'Checker')
        finally:
            session.close()

if __name__ == '__main__':
    unittest.main()
