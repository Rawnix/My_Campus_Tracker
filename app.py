from flask import Flask, render_template, redirect, request, session, url_for
from flask_mysqldb import MySQL
from datetime import datetime
from passlib.hash import sha256_crypt

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

@app.route('/toggle/<string:b>', methods=['GET', 'POST'])
def toggle(b):
    if request.method == 'POST':
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
                return redirect(url_for('password_fail'))

        # if no user found in db
        else:
            return redirect(url_for('username_fail'))


if __name__ == "__main__":
    app.secret_key = "secret123"
    app.run(debug=True)
