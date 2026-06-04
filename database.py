import os
import pyodbc

def conectar():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.environ.get('DB_HOST')};"
        f"DATABASE={os.environ.get('DB_NAME')};"
        f"UID={os.environ.get('DB_USER')};"
        f"PWD={os.environ.get('DB_PASSWORD')};"
        f"Encrypt=yes;"  
        f"TrustServerCertificate=no;" 
        f"Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)