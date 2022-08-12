import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///birthdays.db")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        # Add the user's entry into the database
        message = ""
        name = request.form.get("name")
        month = request.form.get("month")
        day = request.form.get("day")
        if not name:
            message = "Missing name"
        elif not month:
            message = "Missing month"
        elif not day:
            message = "Missing day"
        else:
            db.execute(
                "INSERT INTO birthdays (name, month, day) VALUES(?, ?,?)",
                name,
                month,
                day,
            )

        birthdays = db.execute("SELECT * FROM birthdays")
        if len(message) > 0:
            return render_template("index.html", message=message, birthdays=birthdays)
        else:
            return redirect("/")

    else:
        data = db.execute("SELECT * FROM birthdays")
        return render_template("index.html", birthdays = data)



@app.route("/delete", methods=["POST"])
def deleteBirthDay():
    data = request.get_json(force = True)
    print(f"data: {data}")

    res = False
    id = data['id']
    if id:
        db.execute(f"DELETE FROM birthdays WHERE Id = {id}")
        res = True

    return jsonify({"result": res})

@app.route("/edit", methods=["POST"])
def editBirthday():

        data = request.get_json(force = True)
        res = False
        b_id = data['id']
        message = ""

        name = data["name"]
        month = data["month"]
        day = data["day"]
        if not name:
            message = "Missing name"
        elif not month:
            message = "Missing month"
        elif not day:
            message = "Missing day"
        else:
            print(f"UPDATE birthdays SET name = '{name}', month = {month}, day = {day} WHERE id = {b_id}")
            db.execute(f"UPDATE birthdays SET name = '{name}', month = {month}, day = {day} WHERE id = {b_id}")
            res = True

        return jsonify({
            "result": res,
            "message" : message
        })