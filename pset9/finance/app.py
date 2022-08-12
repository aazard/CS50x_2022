import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
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
# creating history
#db.execute("CREATE TABLE history (id INTEGER PRIMARY KEY, user_id INTEGER, symbol varchar(10), name TEXT, shares INTEGER, price REAL, action TEXT,date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id))")
# creating
#db.execute("CREATE TABLE portfolio (id INTEGER PRIMARY KEY, user_id INTEGER, symbol varchar(10), name TEXT, shares INTEGER, price, REAL, TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id) )")
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    usr = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?", user_id)

    cash_in_total = 0
    for p in portfolio:
        p["act"] = lookup(p['symbol'])['price']
        if p["act"] < p['price']:
            p["class"] = "falling"
        elif p["act"] > p["price"]:
            p["class"] = "rising"
        else:
            p["class"] = "stabel"
        cash_in_total += p["act"] * p["shares"]

    cash_in_total += usr[0]["cash"]
    return render_template("index.html", user=usr[0], portfolio=portfolio, total=cash_in_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        print(symbol)
        try:
            if int(shares) < 0:
                return apology("shares must be positiv", 400)
        except:
            return apology("shares must be a number", 400)

        data = lookup(symbol)
        if not data:
            return apology("invalid symbol", 400)

        user = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])
        current_cash = user[0]["cash"]

        # Calculate amount required to buy shares
        price = data["price"] * int(shares)

        # Check if user has enough money
        if price > current_cash:
            return apology("not enough money", 400)

        # Subtract price from user's cash
        current_cash = current_cash - price

        # Insert new cash into users database
        db.execute("UPDATE users SET cash = :current_cash WHERE id = :user_id",
                   user_id=session["user_id"], current_cash=current_cash)

        # Insert transaction into transactions database
        db.execute("INSERT INTO history (user_id, symbol, name, shares, price, action) VALUES(:user_id, :symbol, :name, :shares, :price, :action)",
                   user_id=session["user_id"],
                   symbol=symbol,
                   name=data['name'],
                   shares=shares,
                   price=data["price"],
                   action="buy")

        # add to portfolio
        db.execute("INSERT INTO portfolio (user_id, symbol, name, shares, price) VALUES(:user_id, :symbol, :name, :shares, :price)",
                   user_id=session["user_id"],
                   symbol=symbol,
                   name=data['name'],
                   shares=shares,
                   price=data["price"])

        flash("Bought!")
        return redirect("/")
    else:
        data = request.args.get('stock')
        return render_template("buy.html", data=data)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    data = db.execute("SELECT * FROM history WHERE user_id = ?", user_id)
    return render_template("history.html", history=data)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)
        else:
            data = lookup(request.form.get("symbol"))
            if data:
                return render_template("quote.html", data=data)
            else:
                return apology("invalid symbol", 400)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation of password", 400)
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("password and confirmation must match", 400)
        else:
            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
            if len(rows) > 0:
                return apology("username already exists", 400)
            else:
                pw_hash = generate_password_hash(request.form.get("password"))
                id = db.execute(
                    "INSERT INTO users(username, hash) VALUES(?, ?)",
                    request.form.get("username"),
                    pw_hash
                )
                if id != 0:
                    return redirect("/login")
                else:
                    return apology("wasn't able to register", 400)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        try:
            shares = int(shares)
            if shares < 1:
                return apology("shares must be a positive integer")
        except ValueError:
            return apology("shares must be a positive integer")
        if not symbol:
            return apology("missing symbol")

        stocks = db.execute(
            "SELECT SUM(shares) as shares, id FROM portfolio WHERE user_id = ? AND symbol = ?;",
            session["user_id"],
            symbol,
        )[0]

        if shares > stocks["shares"]:
            return apology("You don't have this number of shares")
        data = lookup(symbol)
        price = data["price"]
        shares_value = price * shares

        db.execute("INSERT INTO history (user_id, symbol, name, shares, price, action) VALUES(:user_id, :symbol, :name, :shares, :price, :action)",
                   user_id=session["user_id"],
                   symbol=symbol,
                   name=data['name'],
                   shares=shares,
                   price=data["price"],
                   action="sell")

        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            shares_value,
            session["user_id"],
        )

        if stocks["shares"] == shares:
            # delete
            db.execute("DELETE FROM portfolio WHERE id = ?", stocks["id"])
        else:
            # decrement
            db.execute("UPDATE portfolio SET shares = ? WHERE id = ?", shares, stocks["id"])

        flash("Sold!")
        return redirect("/")
    else:
        user_id = session["user_id"]
        history = db.execute("SELECT * FROM history WHERE user_id = ? GROUP BY symbol", user_id)
        data = request.args.get('stock')
        return render_template("sell.html", history=history, data=data)


@app.route("/add", methods=["GET", "POST"])
def addCash():
    if request.method == "POST":
        cash_to_add = request.form.get("cash")
        user_id = session["user_id"]

        # Update cash for user
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", cash_to_add, user_id)

        # Adding to history
        db.execute("INSERT INTO history (user_id, symbol, name, shares, price, action) VALUES(:user_id, :symbol, :name, :shares, :price, :action)",
                   user_id=session["user_id"],
                   symbol="CASH",
                   name="Cash",
                   shares=1,
                   price=cash_to_add,
                   action="cash")

        return redirect("/")
    else:
        return render_template("add.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
