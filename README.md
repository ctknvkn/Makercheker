Steps to Test:
Save the script to a file, e.g., test_transaction_system_sql_server.py.

Ensure you have Python installed along with the pyodbc package:

bash

Copy
pip install pyodbc
Adjust the database connection details (server, database, username, password) in the DatabaseConnection class.

Run the script from the command line:

bash

Copy
python test_transaction_system_sql_server.py
This script sets up the connection to a SQL Server database, combines the main functionality with the unit tests, and uses unittest to ensure all features work as intended. Happy testing! 
