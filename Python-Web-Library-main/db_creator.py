import mysql.connector
import app_config
db_host = app_config.db_host
db_user = app_config.db_user
db_password = app_config.db_password
def create_db():
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password
    )
    cursor = connection.cursor()
    veritabani_adi = "library"
    cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(veritabani_adi))
    cursor.close()
    connection.close()
    mydb = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database="library"
    )
    mycursor = mydb.cursor()
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INT AUTO_INCREMENT PRIMARY KEY,
            serial_number INT,
            owned_id INT,
            rent_Date DATETIME,
            last_date DATETIME
        )
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS book_logs (
            book_id INT,
            serial_number INT,
            book_name VARCHAR(100),
            owned_id INT,
            rent_Date DATETIME,
            last_date DATETIME
        )
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS USERS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100) not null,
            username VARCHAR(100),
            banned boolean
        )
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS REQUESTS (
            USER_ID INT,
            USER_NAME VARCHAR(100),
            SERIAL_NUMBER INT,
            BOOK_NAME VARCHAR(100),
            REQ_DATE DATETIME
        )
    """)   
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS REQUESTS_drop (
            USER_ID INT,
            USER_NAME VARCHAR(100),
            BOOK_ID INT,
            BOOK_NAME VARCHAR(100),
            REQ_DATE DATETIME
        )
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS COMMENTS (
            user_id int,
            serial_number int,
            star decimal(2,0),
            cmnt text,
            deleted boolean
        )
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS unique_books (
            serial_number INT PRIMARY KEY,
            book_name VARCHAR(100),
            link VARCHAR(1024),
            title TEXT,
            writer varchar(100),
            category int,
            page_count int
        )
    """)
    mycursor.close()
    mydb.close()