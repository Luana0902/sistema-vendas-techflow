import mysql.connector


def conectar():
    return mysql.connector.connect(
        host="172.16.78.160",
        port=3306,
        user="leticia",
        password="leticia123",
        database="db_techvarejo"
    )