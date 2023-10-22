from flask import Flask, render_template, url_for, request, flash, redirect, session
from flask_session import Session
import random
from datetime import datetime,timedelta
from models import *
from app import db_host,db_password,db_user,db_table as db_database
import mysql.connector

def kitap_uyarı(user_id):
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )

    cursor = connection.cursor()

    update_query = (
        "SELECT book_name, last_date FROM books INNER JOIN unique_books ON books.serial_Number = unique_books.serial_Number WHERE books.owned_id = "+str(user_id)
    )

    cursor.execute(update_query)
    logs = cursor.fetchall()
    lab = "Teslim Tarihi Yaklaşan Kitaplarınız Var! : "
    temp = False
    for i in logs:
        now = datetime.now()
        if now + timedelta(days=5) > i[1]:
            diff = i[1] - now
            days_remaining = diff.days
            lab += str(days_remaining) + " Gün Kaldı : " + str(i[0]) + " |!|!|!| "
            temp = True
    if temp:
        flash(lab,category="info")
    cursor.close()
    connection.close()

def mysql_commit(update_query,items=None):

    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )

    cursor = connection.cursor()

    if items is None:
        cursor.execute(update_query)
    else:
        cursor.execute(update_query, items)

    connection.commit()
    cursor.close()
    connection.close()

def mysql_query(query):
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )

    cursor = connection.cursor()
    
    cursor.execute(query)
    result = cursor.fetchall()
    
    cursor.close()
    connection.close()

    return result

def mysql_q(query, params=None):
    try:
        connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
        )

        cursor = connection.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        return rows
    except:
        pass
    
def update_database():
    Banned = mysql_q("SELECT ID FROM USERS WHERE BANNED = 1")
    Bans = []
    temp = []
    for i in Banned:
        Bans.append(i[0])
    IDS = mysql_q("SELECT OWNED_ID FROM BOOKS WHERE OWNED_ID IS NOT NULL AND last_date < NOW();")

    for i in IDS:
        temp.append(i[0])
        qry = "UPDATE USERS SET banned = 1 WHERE id = "+str(i[0])
        mysql_commit(qry)
    for i in Bans:
        if i in temp:
            pass
        else:
            qry = "UPDATE USERS SET BANNED = 0 WHERE ID = "+str(i)
            mysql_commit(qry)

stock_data = []

def res_stock():
    global stock_data
    stock_data.clear()
    for i in mysql_q("SELECT serial_number FROM books WHERE owned_id IS NULL"):
        stock_data.append(i[0])
    

def get_stock(serial_num):
    for i in stock_data:
        if i == serial_num:
            return True
    return False

    

def search(arr,x):
    for i in arr:
        print(i[0]," ",x)
        i = i[0]
        if str(i) == str(x):
            print(x," :Done")
            return True
    return False

def cntr(serials,serial):
    for i in serials:
        if i[0] == int(serial):
            return True
    return False

def control_prods(prods,myid):
    for i in prods:
        if i[1] == myid:
            return None
        elif i[1] == None:
            return i
    return None

bks = []
def get_db_books():
    bks.clear()
    books = mysql_q("SELECT * FROM unique_books LEFT JOIN books ON unique_books.serial_Number = books.serial_Number ORDER BY unique_books.BOOK_NAME")
    for i in books:
        tempBook = Book(i[7], i[0], i[1], i[9], i[2], i[10] , i[11],get_stock(i[0]),i[3],i[4],i[5],i[6])
        bks.append(tempBook)
    return bks

def first_date(prods):
    date = prods[0][1].strftime("%Y%m%d%H%M%S")
    stored_id = 0
    j = -1
    for i in prods:
        if i[1] != None:
            j+=1
            da = i[1].strftime("%Y%m%d%H%M%S")
            if da < date:
                date = da
                stored_id = j
    return prods[stored_id][1].strftime("Tarih:%d-%m-%Y Saat:%H:%M:%S")

def make_one(arr):
    filteredBooks = []
    tid = -1
    for i in arr:
        if tid != i.serial:
            filteredBooks.append(i)
            tid = i.serial
    return filteredBooks

def get_lib(arr,id):
    filtered = []
    for j in arr:
        if j.owner == id:
            filtered.append(j)
    return filtered

def options(serial):
    qry = "select book_id,owned_id,last_Date from books where serial_number = "+str(serial)
    temp = mysql_q(qry)
    selected_book_ids = []
    for i in temp:
        a = mysql_q("select username from users where id = "+str(i[1]))
        arr = []
        arr.clear()
        for j in i:
            arr.append(j)
        if a:
            arr.append(a[0][0])
        else:
            arr.append(a)
        selected_book_ids.append(arr)
    return selected_book_ids

def add_book(serial):
    query = "INSERT INTO books (serial_number) values("+str(serial)+");"
    mysql_commit(query)


def delete_book(book_id):
    query = "delete from books where book_id ="+str(book_id)
    mysql_commit(query)

def clean_book(book_id):
    QUER = "SELECT RENT_DATE FROM BOOKS WHERE BOOK_ID = "+str(book_id)
    a = mysql_query(QUER)
    update_query = "UPDATE books SET rent_date = NULL, last_date = NULL, owned_id = NULL WHERE book_id = "+str(book_id)
    mysql_commit(update_query)
    update_query = "UPDATE book_logs SET last_date = CURRENT_TIMESTAMP() WHERE book_id = "+str(book_id)+" and rent_date = '"+str(a[0][0])+"';"
    flash("Kitap Alındı",category="success")

def get_unused_serial_number():
    while True:
        try:
            random_serial = random.randint(1, 999999)
            select_query = "SELECT * FROM books WHERE serial_number = "+str(random_serial)
            result = mysql_q(select_query)
            if not result:
                return random_serial
        
        except:
            print("Error")
        
def request_book(book_id,user_id,user_name,serial_number):
    qry = "SELECT banned FROM USERS WHERE ID = "+str(user_id)
    ban = mysql_q(qry)
    if ban == 1:
        flash("İADE EDİLMEMİŞ KİTAPLARINIZ VAR!!",category="error")
        return None
    user_name = user_name[0][0]
    QRY = "SELECT USER_ID FROM REQUESTS WHERE USER_ID = "+str(user_id)+" AND serial_number = "+str(serial_number)
    q = mysql_q(QRY)
    if q == []:
        QRYY = "SELECT serial_number FROM BOOKS WHERE BOOK_ID = "+str(book_id)
        book_data = mysql_q(QRYY)[0]
        QR = "SELECT BOOK_NAME FROM UNIQUE_BOOKS WHERE SERIAL_NUMBER = "+str(book_data[0])
        book_data2 = mysql_q(QR)[0]
        QRY = "INSERT INTO REQUESTS VALUES ("+str(user_id)+", '"+str(user_name)+"',"+str(book_data[0])+",'"+str(book_data2[0])+"', CURRENT_TIMESTAMP())"
        mysql_commit(QRY)
        flash("İstek Gönderildi",category="success")
    else:
        flash("Zaten İstek Gönderdiniz!",category="error")

def request_drop(book_id,user_id,username):
    QRY = "SELECT BOOK_ID FROM REQUESTS_DROP WHERE BOOK_ID = "+str(book_id)
    A = mysql_q(QRY)
    if not(A):
        qq = "SELECT unique_books.BOOK_NAME FROM BOOKS INNER JOIN unique_books ON books.serial_Number = unique_books.serial_Number WHERE books.BOOK_ID = "+str(book_id)
        book_name = mysql_q(qq)[0][0]
        QR = "INSERT INTO REQUESTS_DROP VALUES("+str(user_id)+",'"+str(username)+"',"+str(book_id)+",'"+str(book_name)+"',CURRENT_TIMESTAMP())"
        mysql_commit(QR)
        flash("Bırakma isteği gönderildi",category="success")
    else:
        flash("İsteği zaten gönderdiniz!",category="error")

def drop_book(book_id):
    QUER = "SELECT RENT_DATE FROM BOOKS WHERE BOOK_ID = "+str(book_id)
    a = mysql_query(QUER)
    update_query = "UPDATE books SET rent_date = NULL, last_date = NULL, owned_id = NULL WHERE book_id = "+str(+book_id)
    mysql_commit(update_query)
    update_query = "UPDATE book_logs SET last_date = CURRENT_TIMESTAMP() WHERE book_id = "+str(book_id)+" and rent_date = '"+str(a[0][0])+"';"
    mysql_commit(update_query)