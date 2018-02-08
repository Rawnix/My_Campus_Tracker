from flask import Flask, render_template, redirect, request, session, url_for
from flask_mysqldb import MySQL
from datetime import datetime
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'mct'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def getcolor(n):
    if str(n) == "available" or str(n) == "open":
        return "green"
    else:
        return "red"

@app.route('/')
def index():
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM status;")
    result = cur.fetchall()


    """ 0:dispensary  1:doctor  2:sbi_atm_cash """
    # store the statuses of buildings
    # ds = result[0]['stat']
    # dds = result[1]['stat']
    # ss = result[2]['stat']
    # store color (green or red)
    # dsc = getcolor(ds)
    # ddsc = getcolor(dds)
    # ssc = getcolor(ss)
    # store

    # store colors:
    colors = [1, 2, 3]
    for i in range(3):
        colors[i] = getcolor(result[i]['stat'])

    mysql.connection.commit()
    cur.close()
    # if request.method == ['POST']:
    #
    # else:
    return render_template('home.html', result=result, colors=colors)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/login')
    return wrap

# common route for toggling any status
@app.route('/toggle/<string:b>', methods=['GET', 'POST'])
@is_logged_in
def toggle(b):
    if request.method == 'POST' and session['logged_in']:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM status WHERE building = %s", [b])
        row = cur.fetchone()

        # interchange avail and unavail & open and closed
        status = row['stat']
        if status=="available":
            status = "unavailable"
        elif status=="unavailable":
            status = "available"
        elif status=="open":
            status = "closed"
        else:
            status = "open"

        # change the status in the db also add the clg_id of user who toggled and also datetime
        cur.execute("UPDATE status SET stat = %s, clg_id = %s, upd_time = %s WHERE building = %s;", [status, session['clg_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), b])

        mysql.connection.commit()
        cur.close()
        return redirect('/')
    elif request.method == 'GET':
        return redirect('/')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        # store the username and password from the form
        u = request.form['username']
        p = request.form['password']

        # open connection
        cur = mysql.connection.cursor()
        # select rows from table of given user
        cur.execute("SELECT * FROM users WHERE clg_id = %s", [u])
        # store the first(and only) row from table in "row"
        row = cur.fetchone()

        # close connection
        mysql.connection.commit()
        cur.close()

        # check if a user is found
        if row > 0:
            pswd = row['hash']
            if sha256_crypt.verify(p, pswd):
                session['clg_id'] = row['clg_id']
                session['logged_in'] = True
                return redirect("/")
            else:
                return render_template('password_fail.html')

        # if no user found in db
        else:
            return render_template('username_fail.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        u = request.form['username']
        # check if provided username is not present in users table
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE clg_id = %s", [u])
        row = cur.fetchone()
        if row > 0:
            mysql.connection.commit()
            cur.close()
            return render_template('username_exists.html')
        else:
            f = request.form['first_name']
            l = request.form['last_name']
            e = request.form['email_id']
            p = request.form['password']
            r = request.form['re_password']

            if p!=r:
                return ("Passwords don't match!")
            else:
                # generate hash
                p = sha256_crypt.encrypt(str(p))
                # add user in the users table db
                cur.execute("INSERT INTO users(clg_id, first_name, last_name, email_id, hash) VALUES(%s, %s, %s, %s, %s)", [u, f, l, e, p])
                mysql.connection.commit()
                cur.close()
                return render_template('registered.html')

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'GET':
        return render_template('buy.html')
    else:
        s = request.form['subject']
        t = request.form['title']

        cur = mysql.connection.cursor()
        if t != '':
            cur.execute("SELECT * FROM books WHERE subject = %s AND title = %s;", [s, t])
        else:
            cur.execute("SELECT * FROM books WHERE subject = %s;", [s])

        rows = cur.fetchall()

        mysql.connection.commit()
        cur.close()

        if rows > 0:
            return render_template('buy_query.html', rows=rows)
        else:
            return render_template("Sorry, no results found.")

@app.route('/sell', methods=['GET', 'POST'])
@is_logged_in
def sell():
    if request.method == 'GET':
        return render_template('sell.html')
    else:
        s = request.form['subject']
        t = request.form['title']
        a = request.form['author']
        h = request.form['hostel']
        r = request.form['room_num']
        m = request.form['mob_num']
        p = request.form['price']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO books (subject, title, author, seller_clg_id, hostel, room_num, mob_num, price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [s, t, a, session['clg_id'], h, r, m, p])

        mysql.connection.commit()
        cur.close()

        return redirect('/my_sale')

@app.route('/my_sale')
@is_logged_in
def my_sale():
    # redirect to login page if not already logged in
    if session['clg_id'] == '':
        return redirect("/login")
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM books WHERE seller_clg_id = %s", [session['clg_id']])
        rows = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        if rows > 0:
            return render_template('my_sale.html', rows=rows)
        else:
            return render_template("You have not put any book up for sale.")

@app.route('/logout')
@is_logged_in
def logout():
    # session['logged_in'] = False
    # session['clg_id'] = ''
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.secret_key = "secret123"
    app.run(debug=True)
