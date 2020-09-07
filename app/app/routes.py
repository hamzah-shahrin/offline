import requests
import os
from app import app
from app.forms import RequestForm
from app.scraper import create_book
from flask import render_template, send_from_directory, flash, redirect, request

dark = False


@app.route("/")
@app.route("/light", methods=["GET", "POST"])
def index():
    global dark
    dark = False

    form = RequestForm()
    if form.validate_on_submit():
        data = request.form['url']
        if data is None:
            flash("No URL entered")
        return redirect('/download/' + data)
    return render_template("index.html", title="Offline", form=form, dark=False)


@app.route("/dark", methods=["GET", "POST"])
def index_d():
    global dark
    dark = True

    form = RequestForm()
    if form.validate_on_submit():
        data = request.form['url']
        if data is None:
            flash("No URL entered")
        return redirect('/download/' + data)
    return render_template("index.html", title="Offline", form=form, dark=True)


@app.route("/download/<path:url>")
def download(url):
    global dark

    try:
        create_book(url)
        path = os.path.join(app.root_path, 'static\\epub')
        filename = len(os.listdir(path))
        return send_from_directory(path, filename=str(filename)+'.epub',
                                   as_attachment=True)
    except FileNotFoundError:
        return render_template("error.html", dark=dark)
    except (requests.exceptions.ConnectionError, requests.exceptions.InvalidSchema):
        return render_template("error.html", dark=dark)
