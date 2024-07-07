import os
from tkinter.messagebox import NO

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

db.execute("CREATE TABLE IF NOT EXISTS 'users' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'username' TEXT NOT NULL, 'hash' TEXT NOT NULL, 'cash' NUMERIC NOT NULL DEFAULT 10000.00 )")
db.execute("CREATE TABLE IF NOT EXISTS 'log' ('user_id' integer NOT NULL, 'username' text NOT NULL, 'stocks' varchar(6), 'price' double precision, 'time' datetime DEFAULT CURRENT_TIMESTAMP, 'number' INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS 'users_data' ('user_id' bigint, 'symbol' varchar(6), 'number' integer)")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # get data
    user_data = db.execute("SELECT * FROM users_data WHERE user_id=:user_id", user_id=session['user_id'])
    user_acc_data = db.execute("SELECT * FROM users WHERE id=:user_id", user_id=session['user_id'])

    cash = user_acc_data[0]['cash']
    total_cash = cash

    html_data = []


    for i, val in enumerate(user_data):
        symbol_info = lookup(user_data[i]['symbol'])

        symbol = symbol_info['symbol']
        name = symbol_info['name']
        num_of_shares = user_data[i]['number']
        price = symbol_info['price']
        price_total = price * num_of_shares

        total_cash += price_total

        html_data.append({
            "symbol" : symbol,
            "name" : name,
            "num_of_shares" : num_of_shares,
            "price" : usd(price),
            "price_total" : usd(price_total),
        })

    return render_template("index.html", user_data=html_data, cash=usd(cash), total_cash=usd(total_cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        symbol_info = lookup(request.form.get("symbol"))
        if not symbol_info:
            return apology("NO SUCH SYMBOL")


        # check if enough money
        num_of_shares = request.form.get("shares")
        for c in num_of_shares:
            if not c.isdigit():
                return apology("UNKNOWN FORMAT")
        num_of_shares = int(num_of_shares)
        cash_needed = symbol_info['price'] * num_of_shares
        user_info = db.execute("SELECT * FROM 'users' WHERE id=:user_id", user_id=session['user_id'])
        if cash_needed > user_info[0]['cash']:
            return apology("NOT ENOUGH MONEY")


        # update cash value
        current_cash = user_info[0]['cash'] - cash_needed
        db.execute("UPDATE 'users' SET 'cash' = :current_cash WHERE id = :user_id",
                    current_cash=current_cash, user_id=session['user_id'])


        # update user data
        user_data = db.execute("SELECT * FROM users_data WHERE user_id=:user_id AND symbol=:symbol",
                                user_id=session['user_id'], symbol=symbol_info['symbol'])
        if user_data == None or user_data == []:
            # user doesn't have these shares. create
            db.execute("INSERT INTO 'users_data' ('user_id', 'symbol', 'number') \
                    VALUES (:user_id, :symbol, :number)", user_id=session['user_id'],
                    symbol=symbol_info['symbol'], number=num_of_shares)
        else:
            # user have them. rewrite
            current_number_of_shares = user_data[0]['number'] + num_of_shares
            db.execute("UPDATE users_data SET number=:number WHERE user_id=:user_id AND symbol=:symbol",
                        number=current_number_of_shares, user_id=session['user_id'], symbol=symbol_info['symbol'])


        # create a log
        db.execute("INSERT INTO 'log' ('user_id', 'username', 'stocks', 'price', 'number') \
                    VALUES (:user_id, :username, :stocks, :price, :num_of_shares)",
                    user_id=user_info[0]['id'], username=user_info[0]['username'],
                    stocks=symbol_info['symbol'], price=-cash_needed, num_of_shares=num_of_shares)

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    username = request.args.get("username")
    if username == None or len(username) == 0:
            return jsonify(False)

    db_request_info = db.execute("SELECT * FROM users WHERE username=:username", username=username)

    if db_request_info != None and db_request_info != []:
        return jsonify(False)

    return jsonify(True)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    log = db.execute("SELECT * FROM log WHERE user_id=:user_id", user_id=session['user_id'])
    log_refactored = []
    for dictionary in log:
        log_refactored.append({
            "symbol" : dictionary['stocks'],
            "number" : dictionary['number'],
            "price_each" : usd(abs(dictionary['price'] / dictionary['number'])),
            "price_total" : '-' + usd(abs(dictionary['price'])) if dictionary['price']<0 else usd(dictionary['price']),
            "time" : dictionary['time'],
        })

    return render_template("history.html", log=log_refactored)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        symbol_info = lookup(symbol)
        if not symbol_info:
            return apology("NO SUCH SYMBOL")

        text = f'A share of {symbol_info["name"]} ( {symbol_info["symbol"]} ) costs {usd(symbol_info["price"])}'
        return render_template("quoted.html", text=text)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # get data
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirm = request.form.get("confirmation")

        if not username:
            return apology("MUST PROVIDE USERNAME")
        elif not password or not password_confirm:
            return apology("MUST PROVIDE PASSWORD")
        elif password != password_confirm:
            return apology("PASSWORDS MUST MATCH")

        users = db.execute("SELECT * FROM users WHERE username=:username", username=username)
        if users != None and users != []:
            return apology("USERNAME IS TAKEN")

        password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        # add user to data base
        user_id = db.execute('''INSERT INTO "users" ("id","username","hash") VALUES (NULL, :username, :password_hash)''',
                    username=username, password_hash=password_hash)

        session["user_id"] = user_id
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":

        # get data
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        user_acc_data = db.execute("SELECT * FROM users WHERE id=:user_id", user_id=session['user_id'])
        user_data = db.execute("SELECT * FROM users_data WHERE user_id=:user_id AND symbol=:symbol",
                                user_id=session['user_id'], symbol=symbol)

        if user_data[0]['number'] < shares:
            return apology("NOT ENOUGH SHARES")


        symbol_info = lookup(symbol)

        if user_data[0]['number'] - shares == 0:
            db.execute("DELETE FROM users_data WHERE symbol=:symbol", symbol=symbol)
        else:
            db.execute("UPDATE users_data SET number=:number WHERE user_id=:user_id AND symbol=:symbol",
                        number=user_data[0]['number'] - shares, user_id=session['user_id'], symbol=symbol)

        cashback = user_acc_data[0]['cash'] + symbol_info['price']*shares
        db.execute("UPDATE users SET cash=:cash WHERE id=:user_id",
                    cash=cashback, user_id=session['user_id'])


        # create a log
        db.execute("INSERT INTO 'log' ('user_id', 'username', 'stocks', 'price', 'number') \
                    VALUES (:user_id, :username, :stocks, :price, :num_of_shares)",
                    user_id=user_acc_data[0]['id'], username=user_acc_data[0]['username'],
                    stocks=symbol_info['symbol'], price=symbol_info['price']*shares, num_of_shares=-(user_data[0]['number'] - shares))


        return redirect("/")

    else:
        user_data = db.execute("SELECT * FROM users_data WHERE user_id=:user_id", user_id=session['user_id'])
        return render_template("sell.html", user_data=user_data)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
