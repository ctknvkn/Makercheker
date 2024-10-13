To run the code effectively, follow these steps and ensure you have the necessary prerequisites:

Prerequisites
Python: Make sure Python is installed (preferably version 3.6 or later).
SQLAlchemy: Install SQLAlchemy for ORM functionality.
PyODBC: Install PyODBC to connect to SQL Server.
SQL Server: Ensure you have access to a SQL Server database.

Configure Database:

Ensure the SQL Server is running and accessible.
Create a database if it doesn't exist.
Adjust the DATABASE_URI in the code to match your SQL Server details. It is using SQL server AD authentication, please adjust authentication according to the environment you are running

Steps to Run the Code
Verify Database Connection:

Test the connection using the DATABASE_URI to ensure it’s correctly configured.
Prepare Database Schema:

The code will automatically create tables using SQLAlchemy's Base.metadata.create_all(engine) method. Ensure the database user has permission to create tables.
Run the Script:

Open a terminal in VSCode or your preferred IDE.
Execute the script:
bash
python Kannappan_MakerChekerFinal.py
Check Logs:

Monitor the terminal for logs and debug messages to verify operations.
