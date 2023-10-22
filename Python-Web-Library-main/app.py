from flask import Flask, render_template, url_for, request, flash, redirect, session
from flask_session import Session
import functions as fx
from models import *
import secrets
import app_config
import mysql.connector
import db_creator

db_host = app_config.db_host
db_user = app_config.db_user
db_password = app_config.db_password
db_table = app_config.db_table
db_creator.create_db()

CLIENT_SECRET = app_config.CLIENT_SECRET
APPLICATION_ID = app_config.APPLICATION_ID
REDIRECT_URI = app_config.REDIRECT_URI
AUTHORITY_URL = app_config.AUTHORITY_URL
AUTHORITY = app_config.AUTHORITY
endpoint = app_config.ENDPOINT

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_bytes(32)
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)
allBooks = []
books = []
SCOPES = ['User.Read', 'User.ReadBasic.All']
import msal
client_instance = msal.ConfidentialClientApplication(
    client_id=APPLICATION_ID,
    client_credential=CLIENT_SECRET,
    authority=AUTHORITY_URL
)

admins = []

PAGE = 0
ITEMS_PER_PAGE = 24
def lock_next(items):
    number = 0
    for i in items:
        number+=1
    if(number < ITEMS_PER_PAGE):
        return True
    return False

def page_f(arr,reset = False):
    global PAGE
    elements = []
    if reset:
        PAGE = 0
    for i in range(PAGE*ITEMS_PER_PAGE,ITEMS_PER_PAGE*(PAGE+1)):
        try:
            elements.append(arr[i])
        except:
            pass
    return elements

def r_info():
    return render_template("datas.html",admin = session.get('user_id') in admins,username = session.get('user_username'),users = get_most_user(),books = get_most_book())

def r_users():
    arr = fx.mysql_q("select * from users order by email")
    myarr = []
    for i in arr:
        qry = "SELECT * FROM books INNER JOIN unique_books ON books.serial_Number = unique_books.serial_Number WHERE books.owned_id = "+str(i[0])
        bkk = fx.mysql_q(qry)
        myarr.append([i,bkk])
    return render_template('user_page.html',admin = session.get('user_id') in admins,arr = myarr,username = session.get('user_username'))

def res_req():
    try:
        rrq = fx.mysql_q("SELECT * FROM REQUESTS ORDER BY REQ_DATE")
        rrqd = fx.mysql_q("SELECT * FROM REQUESTS_DROP ORDER BY REQ_DATE")
        return render_template('requests.html',reqs = rrq,reqs_d=rrqd,admin = session.get('user_id') in admins,username = session.get('user_username'))
    except:
        return render_template('requests.html',reqs = [],reqs_d = [],admin = session.get('user_id') in admins,username = session.get('user_username'))

def r_sys():
    return render_template('lib.html',allBooks = fx.get_lib(fx.get_db_books(),session.get('user_id')),username = session.get('user_username'),admin = session.get('user_id') in admins)

def r_index():
    allBooks.clear()
    books = fx.mysql_q("SELECT * FROM unique_books LEFT JOIN books ON unique_books.serial_Number = books.serial_Number ORDER BY unique_books.BOOK_NAME")
    fx.res_stock()
    for i in books:
        tempBook = Book(i[7], i[0], i[1], i[9], i[2], i[10] , i[11],fx.get_stock(i[0]),i[3],i[4],i[5],i[6])
        allBooks.append(tempBook)
    global PAGE
    return render_template('index.html',allBooks = page_f(fx.make_one(allBooks)),username = session.get('user_username'),admin = session.get('user_id') in admins,PAGE = PAGE,LOCK = lock_next(page_f(fx.make_one(allBooks))))  

def update_book_info(user_id, serial_number):
        qry = "select * from books where owned_id = "+str(session.get('user_id'))+" and serial_number = "+str(serial_number)
        aa = fx.mysql_q(qry)
        temp  = 0
        for i in aa:
            temp+=1
        if session.get('user_id') == -1:
            return None
        else:
            prods = fx.mysql_q("select book_id,owned_id,serial_number from books where serial_number ="+serial_number)
            if prods == []:
                flash("Bu Kitap Kütüphanede Yok!",category="error")
            if fx.control_prods(prods,session.get('user_id')) != None and temp == 0:
                t,y,z = fx.control_prods(prods,session.get('user_id'))
                fx.request_book(t,session.get('user_id'),session.get('user_username'),z)
            else:
                pp = fx.mysql_q("select serial_number from books where owned_id ="+str(session.get('user_id')))
                if fx.cntr(pp,serial_number):
                    flash("HATA - Ürüne Sahipsiniz",category='error')
                else:
                    pr = fx.mysql_q("select book_id,last_date from books where serial_number ="+serial_number)
                    flash("HATA - Stok Yok! En Yakın     "+fx.first_date(pr),category='error')
            r_index()
            res_req()

def get_most_book():
    a = fx.mysql_q("SELECT serial_number, COUNT(*) AS sayi FROM book_logs GROUP BY serial_number ORDER BY sayi DESC")
    myarr = []
    for i in range(0,a.__len__()):
        if i == 3:
            break;
        if a[i]:
            myarr.append(a[i])
    return myarr

def get_most_user():
    a = fx.mysql_q("SELECT owned_id, COUNT(*) AS sayi FROM book_logs GROUP BY owned_id ORDER BY sayi DESC")
    myarr = []
    for i in range(0,a.__len__()):
        if i == 3:
            break;
        if a[i]:
            myarr.append(a[i])
    return myarr

def delete_req(user_id,SERIAL):
    try:
        QRY = "DELETE FROM REQUESTS WHERE USER_ID = "+str(user_id)+" and SERIAL_NUMBER = "+str(SERIAL)+";"
        fx.mysql_commit(QRY)
    except:
        flash("Silinemedi!",category="error")

def delete_req_d(user_id,BOOK_ID):
    try:
        QRY = "DELETE FROM REQUESTS_DROP WHERE USER_ID = "+str(user_id)+" and BOOK_ID = "+str(BOOK_ID)+";"
        fx.mysql_commit(QRY)
    except:
        flash("Silinemedi!",category="error")

def add_book(t,y,date):
    qry = "SELECT BOOK_ID FROM BOOKS WHERE SERIAL_NUMBER = "+str(y)+" and owned_id = "+str(t)+" ;"
    x = fx.mysql_q(qry)
    qry = "SELECT BOOK_ID FROM BOOKS WHERE SERIAL_NUMBER = "+str(y)+" and owned_id is null"
    aa = fx.mysql_q(qry)
    if not(x == None or x == []):
        flash("Kullanıcı Kitaba Sahip!",category="error")
    elif aa == None or aa == []:
        flash("Bu Kitaptan Kalmadı!!",category='error')
    else:
        qry = "select * from books where owned_id = "+str(t)+" and serial_number = "+str(y)
        aa = fx.mysql_q(qry)
        temp  = 0
        for i in aa:
            temp+=1
        prods = fx.mysql_q("select book_id,owned_id,serial_number from books where serial_number ="+str(y))
        if fx.control_prods(prods,session.get('user_id')) != None and temp == 0:
            q,w,e = fx.control_prods(prods,session.get('user_id'))
            update_query = "UPDATE books SET owned_id = "+str(t)+", rent_date = CURRENT_TIMESTAMP(), last_date = DATE_ADD( CURRENT_TIMESTAMP(),INTERVAL "+str(date)+" DAY) WHERE book_id = "+str(q)
            fx.mysql_commit(update_query)
            queryy = "SELECT * FROM books LEFT JOIN unique_books ON books.serial_Number = unique_books.serial_Number WHERE books.book_id = "+str(q)
            dy = fx.mysql_q(queryy)
            dt = dy[0]
            insert_query = "INSERT INTO book_logs VALUES ("+str(dt[0])+","+str(dt[1])+",'"+str(dt[6])+"',"+str(dt[2])+",'"+str(dt[3])[:19]+"','"+str(dt[4])[:19]+"')"
            fx.mysql_commit(insert_query)
            allBooks.clear()
            books = fx.mysql_q("SELECT * FROM unique_books LEFT JOIN books ON unique_books.serial_Number = books.serial_Number ORDER BY unique_books.BOOK_NAME")
            fx.res_stock()
            for i in books:
                tempBook = Book(i[7], i[0], i[1], i[9], i[2], i[10] , i[11],fx.get_stock(i[0]),i[3],i[4],i[5],i[6])
                allBooks.append(tempBook)
            flash("Kitap Verildi",category="success")
    delete_req(t,y)
    r_info()
    r_sys()
    res_req()
    r_index()

def add_book_d(user_id,book_id):
    qry="DELETE FROM REQUESTS_DROP WHERE BOOK_ID = "+str(book_id)
    fx.mysql_commit(qry)
    fx.clean_book(book_id)
    delete_req_d(user_id,book_id)
    res_req()

def log_google(mymail, myname):
    db_username = fx.mysql_q("select username from users where email = '"+str(mymail)+"'")
    db_email = fx.mysql_q("select email from users where email = '"+str(mymail)+"'")
    db_id = fx.mysql_q("select id from users where email = '"+str(mymail)+"'")
    if fx.search(db_email, mymail):
        print(db_id)
        user = User(db_id, db_email, db_username)
        session['user_id'] = int(str(user.id).replace("[(","").replace(",)]",""))
        session['user_email'] = user.email
        session['user_username'] = user.username
    else:
        query = "INSERT INTO users (email, username, banned) VALUES ('"+str(mymail)+"','"+str(myname)+"',0);"
        fx.mysql_commit(query)
        log_google(mymail, myname)
    return True

def search_f(dataa,selectedOption,cat_option):
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_table
    )
    cursor = connection.cursor()

    qry = "SELECT * FROM unique_books LEFT JOIN books ON unique_books.serial_number = books.serial_number WHERE"
    if cat_option != '-1':
        qry += " category = "+str(cat_option)+" and"
    qry += " unique_books.book_name LIKE '"+str(dataa)+"%'"
    if selectedOption == '0':
        qry += " ORDER BY unique_books.book_name;"
        myprods = fx.mysql_q(qry)
    elif selectedOption == '1':
        qry += " ORDER BY unique_books.book_name DESC;"
        myprods = fx.mysql_q(qry)
    elif selectedOption == '2' or selectedOption == '3':
        qry += " ORDER BY unique_books.book_name;"
        myprods = fx.mysql_q(qry)
        myserials = cursor.execute("SELECT serial_number, COUNT(*) AS sayi FROM book_logs GROUP BY serial_number ORDER BY sayi DESC;").fetchall()
        kitap_id_siralamasi = {kitap_id: siralama for kitap_id, siralama in myserials}

        # Kitapları sıralama bilgisine göre sıralama
        siralanmis_kitaplar = sorted(myprods, key=lambda x: kitap_id_siralamasi.get(x[0], 0))

        myprods = siralanmis_kitaplar
        myprods.reverse()
        if selectedOption == '3':
            myprods.reverse()
    
    cursor.close()
    connection.close()
    allBooks.clear()
    fx.res_stock()
    for i in myprods:
        tempBook = Book(i[7], i[0], i[1], i[9], i[2], i[10] , i[11],fx.get_stock(i[0]),i[3],i[4],i[5],i[6])
        allBooks.append(tempBook)
    global PAGE
    return render_template('index.html',allBooks = page_f(fx.make_one(allBooks),True),username = session.get('user_username'),admin = session.get('user_id') in admins,PAGE = PAGE,LOCK = lock_next(page_f(fx.make_one(allBooks)))) 

def redirect_book(i):
    global myBook
    fx.res_stock()
    myBook = Book(i[7], i[0], i[1], i[9], i[2], i[10] , i[11],fx.get_stock(i[0]),i[3],i[4],i[5],i[6])
    qry = "SELECT STAR FROM COMMENTS where deleted = 0 and serial_number = "+str(myBook.serial)
    stars = fx.mysql_q(qry)
    temp = 0
    count = 0
    for i in stars:
        temp += i[0]
        count += 1
    if count == 0:
        star = "Değerlendirme Yok"
    else:
        ww = temp/count
        star = "{:.1f}".format(ww)
    qry = "SELECT * FROM COMMENTS where deleted = 0 and serial_number = "+str(myBook.serial)
    a = fx.mysql_q(qry)
    qry = "SELECT owned_id FROM BOOK_LOGS WHERE SERIAL_NUMBER = "+str(myBook.serial)+" and owned_id = "+str(session.get('user_id'))
    onay = False
    if fx.mysql_q(qry) != []:
        onay = True
    else:
        onay = False
    return render_template('book.html',book = myBook,admin = session.get('user_id') in admins,username = session.get('user_username'),comments = a,star = star,onay = onay)

def redirect_book_admin(i):
    global myBk
    fx.res_stock()
    myBk = Book(i[7], i[0], i[1], i[9], i[2], i[10] , i[11],fx.get_stock(i[0]),i[3],i[4],i[5],i[6])
    global selected_serial  
    selected_serial = i[0]
    qry = "SELECT STAR FROM COMMENTS where deleted = 0 and serial_number = "+str(myBook.serial)
    stars = fx.mysql_q(qry)
    temp = 0
    count = 0
    for j in stars:
        temp += j[0]
        count += 1
    if count == 0:
        star = "Değerlendirme Yok"
    else:
        ww = temp/count
        star = "{:.1f}".format(ww)
    qry = "SELECT * FROM COMMENTS where deleted = 0 and serial_number = "+str(myBook.serial)
    a = fx.mysql_q(qry)
    return render_template('admin.html',book = myBk,options=fx.options(i[0]),admin = session.get('user_id') in admins,username = session.get('user_username'),star = star,comments = a)

@app.route('/', methods = ['POST','GET'])
def index():
    print(session.get('user_id'))
    fx.res_stock()
    global PAGE
    fx.update_database()
    data = request.form
    if request.method == "POST":
        if 'per_button' in data:
            global ITEMS_PER_PAGE
            ITEMS_PER_PAGE = int(data['per'])
            PAGE = 0
            r_index()
        else:
            try:
                if data['myval'] == '0':
                    PAGE = 0
                    if data['search?'] != '1':
                        query ="select * from books where serial_number = "+data['myp']
                        i = fx.mysql_q(query)
                        if session.get('user_id') in admins and 'admin-btn' in data:
                            redirect_book_admin(i[0])
                            return redirect(url_for('admin'))
                        redirect_book(i[0])
                        return redirect(url_for('book'))
                    else:
                        selected_option = data['sortOption']
                        selected_cat = data['cat_option']
                        search_f(data['myp'],selected_option,selected_cat)
                        return redirect(url_for('index'))
                    fx.update_database()
                elif data['myval'] == '1':
                    PAGE -= 1
                    r_index()
                    return redirect(url_for('index'))
                elif data['myval'] == '2':
                    PAGE += 1
                    r_index()
                    return redirect(url_for('index'))
                elif data['myval'] == '3':
                    PAGE = 0
                    r_index()
                    return redirect(url_for('index'))
            except:
                PAGE = 0
                if data['search?'] != '1':
                    query ="SELECT * FROM unique_books LEFT JOIN books ON unique_books.serial_Number = books.serial_Number WHERE unique_books.serial_number = "+data['myp']
                    i = fx.mysql_q(query)
                    redirect_book(i[0])
                    redirect_book_admin(i[0])
                    if session.get('user_id') in admins  and 'admin-btn' in data:
                        return redirect(url_for('admin'))
                    return redirect(url_for('book'))
                else:
                    selected_option = data['sortOption']
                    selected_cat = data['cat_option']
                    search_f(data['myp'],selected_option,selected_cat)
    if session.get('user_id') != None:
        return render_template('index.html',allBooks = page_f(fx.make_one(allBooks)),username = session.get('user_username'),admin = session.get('user_id') in admins,PAGE = PAGE,LOCK = lock_next(page_f(fx.make_one(allBooks))))
    else:
        return redirect(url_for('login'))
    
@app.route('/requests', methods=['POST','GET'])
def requests():
    if request.method == "POST":
        data = request.form
        if 'label-BOOK-ID' in data:
            if 'btn-approve' in data:
                add_book_d(data['label-ID'],data['label-BOOK-ID'])
                res_req()
                r_index()
                redirect(url_for('requests'))
            elif 'btn-deny' in data:
                delete_req_d(data['label-ID'],data['label-BOOK-ID'])
                res_req()
                r_index()
        else:
            if 'btn-approve' in data:
                add_book(data['label-ID'],data['label-SERIAL'],data['label-days'])
                res_req()
                r_index()
                redirect(url_for('requests'))
            elif 'btn-deny' in data:
                delete_req(data['label-ID'],data['label-SERIAL'])
                res_req()
    if session.get('user_id') in admins:
        try:
            rrq = fx.mysql_q("SELECT * FROM REQUESTS ORDER BY REQ_DATE")
            rrqd = fx.mysql_q("SELECT * FROM REQUESTS_DROP ORDER BY REQ_DATE")
            return render_template('requests.html',reqs = rrq,reqs_d=rrqd,admin = session.get('user_id') in admins,username = session.get('user_username'))
        except:
            return render_template('requests.html',reqs = [],reqs_d = [],admin = session.get('user_id') in admins,username = session.get('user_username'))
    else:
        return redirect(url_for('login'))

@app.route('/book', methods=['POST', 'GET'])
def book():
    fx.update_database()
    if request.method == "POST":
        data = request.form
        if 'comment-button' in data:
            qry = "SELECT STAR FROM COMMENTS WHERE deleted = 0 and SERIAL_NUMBER = "+str(data['myp'])+" and user_id = "+str(session.get('user_id'))
            if fx.mysql_q(qry) != []:
                qry = "UPDATE COMMENTS SET DELETED = True WHERE SERIAL_NUMBER = "+str(data['myp'])+" and user_id = "+str(session.get('user_id'))
                fx.mysql_commit(qry)
            qry = "INSERT INTO COMMENTS VALUES("+str(session.get('user_id'))+","+str(data['myp'])+","+str(data['user-star'])+",'"+str(data['user-comment'])+"',0)"
            fx.mysql_commit(qry)
        else:
            if session.get('user_id') != None:
                data = request.form
                update_book_info(session.get('user_id'),data['myp'])
        res_req()
    if session.get('user_id') != None:
        qry = "SELECT STAR FROM COMMENTS where deleted = 0 and serial_number = "+str(myBook.serial)
        stars = fx.mysql_q(qry)
        temp = 0
        count = 0
        for i in stars:
            temp += i[0]
            count += 1
        if count == 0:
            star = "Değerlendirme Yok"
        else:
            ww = temp/count
            star = "{:.1f}".format(ww)
        qry = "SELECT * FROM COMMENTS where deleted = 0 and serial_number = "+str(myBook.serial)
        a = fx.mysql_q(qry)
        qry = "SELECT owned_id FROM BOOK_LOGS WHERE SERIAL_NUMBER = "+str(myBook.serial)+" and owned_id = "+str(session.get('user_id'))  
        onay = False
        if fx.mysql_q(qry) != []:
            onay = True
        else:
            onay = False
        return render_template('book.html',book = myBook,admin = session.get('user_id') in admins,username = session.get('user_username'),comments = a,star = star,onay = onay)
    else:
        return redirect(url_for('login'))
    
@app.route('/users', methods=['POST', 'GET'])
def user_page():
    fx.update_database()
    arr = fx.mysql_q("select * from users order by email")
    if request.method == "POST":
        if session.get('user_id') != None:
            data = request.form
            if 'search_name' in data:
                arr=fx.mysql_q("SELECT * FROM users WHERE username LIKE '"+str(data['myp'])+"%' ORDER BY username;")
            elif 'search_email' in data:
                arr=fx.mysql_q("SELECT * FROM users WHERE email LIKE '"+str(data['myp'])+"%' ORDER BY email;")
            else:
                data = request.form
                fx.update_database()
                fx.clean_book(data['book_id'])
    if session.get('user_id') in admins:
        myarr = []
        for i in arr:
            qry = "SELECT * FROM books LEFT JOIN unique_books ON books.serial_Number = unique_books.serial_Number WHERE books.owned_id = "+str(i[0])
            bkk = fx.mysql_q(qry)
            myarr.append([i,bkk])
        return render_template('user_page.html',admin = session.get('user_id') in admins,arr = myarr,username = session.get('user_username'))
    else:
        return redirect(url_for('login'))

@app.route('/kitap_ekle', methods=['POST', 'GET'])
def kitap_ekle():
    fx.update_database()
    if request.method == "POST":
        if session.get('user_id') != None:
            data = request.form
            name = data['name_bar']
            link = data['link_bar']
            title = data['titles']
            cat_opt = data['cat_selector']
            writer = data['writer']
            page_count = data['page_count']
            num = str(fx.get_unused_serial_number())
            query = "INSERT INTO UNIQUE_BOOKS (serial_number,book_name , link, title,writer,category,page_count) VALUES ("+str(num)+", '"+str(name)+"', '"+str(link)+"','"+str(title)+"','"+str(writer)+"',"+str(cat_opt)+","+str(page_count)+")"
            fx.mysql_commit(query)
            fx.update_database()
            r_sys()
            r_index()
            res_req()
            return redirect(url_for('index'))
    if session.get('user_id') in admins:
        return render_template('kitap_ekle.html',admin = session.get('user_id') in admins,username = session.get('user_username'))
    else:
        return redirect(url_for('login'))

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    fx.update_database()
    silindi = False
    if session.get('user_id') in admins:
        if request.method == "POST":
            data = request.form
            if 'delete-comment' in data:
                qry = "UPDATE COMMENTS SET DELETED = 1 WHERE user_id = "+str(data['comment-user-id'])+" AND serial_number = "+str(data['comment-book-serial'])
                fx.mysql_commit(qry)
            elif data['val'] == '1':
                fx.add_book(data['myp'])
            elif data['val'] == '2':
                fx.delete_book(data['book_id_selector'])
            elif data['val'] == '3':
                name = data['name_bar']
                link = data['link_bar']
                title = data['titles']
                category = data['cat_selector']
                writer = data['writer']
                page_count = data['page_count']
                query = "update unique_books set category = "+category+", writer = '"+str(writer)+"', page_count = "+page_count+" ,book_name = '"+str(name)+"' , link = '"+str(link)+"' , title = '"+str(title)+"' where serial_number = "+str(data['myp'])+";"
                fx.mysql_commit(query)
                r_index()
                r_sys()
                res_req()
                return redirect(url_for('index'))   
            elif data['val'] == '4':
                qry = "SELECT BOOK_ID FROM BOOKS WHERE SERIAL_NUMBER = "+str(data['myp'])
                if fx.mysql_q(qry) != []:
                    flash("Lütfen bütün stokları silin!",category="error")
                else:
                    fx.mysql_commit("DELETE FROM UNIQUE_BOOKS WHERE SERIAL_NUMBER = "+str(data['myp']))
                    r_index()
                    silindi = True
            else:
                update_book_info(session.get('user_id'),data['myp'])
            r_sys()
            r_index()
            res_req()
        qry = "SELECT STAR FROM COMMENTS where deleted = 0 and serial_number = "+str(myBook.serial)
        stars = fx.mysql_q(qry)
        temp = 0
        count = 0
        for i in stars:
            temp += i[0]
            count += 1
        if count == 0:
            star = "Değerlendirme Yok"
        else:
            ww = temp/count
            star = "{:.1f}".format(ww)
        qry = "SELECT * FROM COMMENTS where serial_number = "+str(myBook.serial)
        a = fx.mysql_q(qry)
        if silindi == True:
            silindi = False
            return redirect(url_for('index'))
        return render_template('admin.html',book = myBk,options=fx.options(selected_serial),admin = session.get('user_id') in admins,username = session.get('user_username'),star = star,comments = a)
    else:
        return redirect(url_for('login'))

@app.route('/lib', methods=['POST', 'GET'])
def lib():
    if session.get('user_id') != None:
        fx.kitap_uyarı(session.get('user_id'))
        fx.update_database()
    if request.method == "POST":
        if session.get('user_id') != None:
            try:
                data = request.form
                book_id = data['myp']
                fx.request_drop(book_id,session.get('user_id'),session.get('user_username')[0][0])
                r_sys()
                res_req()
                fx.update_database()
            except:
                r_sys()
                res_req()
                redirect(url_for('lib'))
    if session.get('user_id') != None:
        return render_template('lib.html',allBooks = fx.get_lib(fx.get_db_books(),session.get('user_id')),username = session.get('user_username'),admin = session.get('user_id') in admins)
    else:
        return redirect(url_for('login'))

@app.route("/login")
def login():
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
    return redirect(session["flow"]["auth_uri"])

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config.from_object(app_config)
@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        email = session.get('user')['preferred_username']
        display_name = session.get('user')['name']
        if log_google(email,display_name):
            return redirect(url_for("index"))
        else: return redirect(url_for('login'))
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return redirect(url_for("index"))

@app.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        ).json()
    return render_template('display.html', result=graph_data)


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID, authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=REDIRECT_URI)

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result


app.jinja_env.globals.update(_build_auth_code_flow=_build_auth_code_flow) 


@app.route("/info")
def info():
    book_list = []
    for i in get_most_book():
        a = fx.mysql_q("SELECT * FROM UNIQUE_BOOKS WHERE SERIAL_NUMBER = "+str(i[0]))
        prod = {
            'name' : a[0][1],
            'link' : a[0][2],
            'count' : i[1]
        }
        book_list.append(prod)
    
    user_list = []
    for i in get_most_user():
        print(i)
        b = fx.mysql_q("SELECT * FROM USERS WHERE id = "+str(i[0]))
        print("b:",b)
        prod = {
            'email' : b[0][1],
            'name' : b[0][2],
            'count' : i
        }
        user_list.append(prod)
    return render_template("datas.html",admin = session.get('user_id') in admins,username = session.get('user_username'),users = user_list,books = book_list)

app.config['AUTHORITY'] = AUTHORITY
@app.route("/logout")
def logout():
    try:
        session.clear()  
        post_logout_redirect_uri = url_for("login", _external=True)
        logout_url = f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={post_logout_redirect_uri}"
        return redirect(logout_url)
    except Exception as e:
        return redirect(url_for("login"))

if __name__ == '__main__':
    fx.res_stock()
    books = fx.mysql_q("SELECT * FROM unique_books LEFT JOIN books ON unique_books.serial_Number = books.serial_Number ORDER BY unique_books.BOOK_NAME;")
    for i in books:
        tempBook = Book(i[7], i[0], i[1], i[9], i[2], i[10] , i[11],fx.get_stock(i[0]),i[3],i[4],i[5],i[6])
        allBooks.append(tempBook)
    a = fx.mysql_q("SELECT ID,EMAIL FROM USERS")
    acc = []
    for i in open("admins.txt","r"):
        acc.append(i.replace("\n","").lower())
    for i in a:
        if i[1].lower() in acc:
            admins.append(i[0])
    app.run(debug=True,use_reloader=True,host='0.0.0.0')    