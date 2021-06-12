import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


#Home page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_books")
def get_books():
    books = mongo.db.books.find()
    return render_template("books.html", books=books)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome to All booked, {}".format(request.form.get("username")))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # session user's username from mongo db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


# Add a new book to db
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book = {
            "book_title": request.form.get("book_title"),
            "author": request.form.get("author"),
            "book_description": request.form.get("book_description"),
            "img_url": request.form.get("img_url"),
            "review": request.form.get("review"),
            "reviewed_by": session["user"]
        }
        mongo.db.books.insert_one(book)
        return redirect("/profile/<username>")


# allow user to see book
@app.route("/view_book/<book_title>")
def view_book(book_title):
    book = mongo.db.books.find_one({"_id": ObjectId(book_title)})
    return render_template("view_book.html", book=book)


# Users can edit book
@app.route("/edit_book/<book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if request.method == "POST":
        edited_book = {
            "book_title": request.form.get("book_title"),
            "author": request.form.get("author"),
            "img_url": request.form.get("img_url"),
            "review": request.form.get("review"),
            "created_by": session["user"]
        }
        mongo.db.books.update({"_id": ObjectId(book_id)}, edited_book)

    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template("view_book.html", book=book)


# Delete book
@app.route("/delete_book/<book_id>")
def delete_book(book_id):
    mongo.db.books.remove({"_id": ObjectId(book_id)})
    return redirect("/profile/<username>")


# Render Best Books page
@app.route("/best_books/<username>", methods=["GET", "POST"])
def best_books(username):
    # get the session user's username from database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    # get the session user's books from database
    book_lists = list(mongo.db.book_lists.find({'created_by': username}))

    if session["user"]:
        return render_template(
            "best_books.html", username=username, book_lists=book_lists)

    return redirect(url_for("login"))


# Add a new booklist into database
@app.route("/add_list", methods=["GET", "POST"])
def add_list():
    if request.method == "POST":
        share_list = "on" if request.form.get("share_list") else "off"
        list = {
            "list_name": request.form.get("list_name"),
            "share_list": share_list,
            "created_by": session["user"],
            "books": []
        }
        mongo.db.book_lists.insert_one(list)
        return redirect("/best_books/<username>")


# Render View List Page
@app.route("/view_list/<list_name>")
def view_list(list_name):
    # get book lists from datase
    book_list = mongo.db.book_lists.find_one({"_id": ObjectId(list_name)})
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    # Append new book into a book list
    book_objects_list = []
    for book in book_list['books']:
        book_item = mongo.db.books_in_list.find_one({'_id': ObjectId(book)})
        book_objects_list.append(book_item)

    return render_template(
        "view_list.html",
        book_list=book_objects_list, list=book_list, username=username)


# Edit booklist
@app.route("/edit_list/<list_id>", methods=["GET", "POST"])
def edit_list(list_id):
    if request.method == "POST":

        # Only uptade list_name and share_list fields in the book lists
        mongo.db.book_lists.update_one(
            {"_id": ObjectId(
                list_id)}, {"$set": {"list_name": request.form.get(
                    "list_name"), "share_list": request.form.get(
                        "share_list")}})

    list = mongo.db.book_lists.find_one({"_id": ObjectId(list_id)})
    return redirect(url_for("view_list", list=list, list_name=list["_id"]))


# Delete booklist
@app.route("/delete_list/<list_id>")
def delete_list(list_id):
    mongo.db.book_lists.remove({"_id": ObjectId(list_id)})
    return redirect("/best_books/<username>")


# Add a new book into the database and into a list of books
@app.route("/add_book_in_list/<list_name>", methods=["GET", "POST"])
def add_book_in_list(list_name):
    if request.method == "POST":
        book = {
            "book_name": request.form.get("book_name"),
            "book_author": request.form.get("book_author"),
            "img_url": request.form.get("img_url"),
            "vendor_url": request.form.getlist("vendor_url"),
            "created_by": session["user"]
        }

        # Insert ObjectID from a book into a determined book list
        book_id = mongo.db.books_in_list.insert_one(book).inserted_id
        mongo.db.book_lists.update(
            {'_id': ObjectId(list_name)}, {'$push': {'books': book_id}})

        book_list = mongo.db.book_lists.find_one({"_id": ObjectId(list_name)})

    return redirect(url_for("view_list", list_name=book_list["_id"]))


# Render Book Info page
@app.route("/book_info/<list_name>/<book_name>")
def book_info(list_name, book_name):
    # book_lists = list(mongo.db.book_lists.find()) CHECK IF WILL BE USED
    book = mongo.db.books_in_list.find_one({"_id": ObjectId(book_name)})
    book_list = mongo.db.book_lists.find_one({"_id": ObjectId(list_name)})
    return render_template("book_info.html", book=book, list=book_list)


# Edit book from a booklist
@app.route("/edit_book_in_list/<list_name>/<book_id>", methods=["GET", "POST"])
def edit_book_in_list(list_name, book_id):
    if request.method == "POST":
        edited_book = {
            "book_name": request.form.get("book_name"),
            "book_author": request.form.get("book_author"),
            "img_url": request.form.get("img_url"),
            "vendor_url": request.form.getlist("vendor_url"),
            "created_by": session["user"]
        }
        mongo.db.books_in_list.update({"_id": ObjectId(book_id)}, edited_book)

    book = mongo.db.books_in_list.find_one({"_id": ObjectId(book_id)})
    book_list = mongo.db.book_lists.find_one({"_id": ObjectId(list_name)})
    return render_template("book_info.html", book=book, list=book_list)


# Delete book from a booklist
@app.route("/delete_book_in_list/<list_name>/<book_id>")
def delete_book_in_list(list_name, book_id):
    book_list = mongo.db.book_lists.find_one({"_id": ObjectId(list_name)})
    """
    Delete ObjectID from a book in the 'books' field
    from a specific list of books
    """
    mongo.db.books_in_list.remove({"_id": ObjectId(book_id)})
    mongo.db.book_lists.update(
            {'_id': ObjectId(
                list_name)}, {'$pull': {'books': ObjectId(book_id)}})
    return redirect(url_for("view_list", list_name=book_list["_id"]))


# Render Discover page
@app.route("/discover")
def discover():
    book_lists = list(mongo.db.book_lists.find())
    return render_template("discover.html", book_lists=book_lists)


# Search function
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    book_lists = list(mongo.db.book_lists.find({"$text": {"$search": query}}))
    return render_template("discover.html", book_lists=book_lists)





if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
