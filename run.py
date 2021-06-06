import os
from flask import Flask, render_template


app = Flask(__name__)

#This links to the html pages to avoid writing html in this doc
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


"""
(__main__) is the name of the default module in Python.
the app will be run using the statements in (__main__)
"""
if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True)


