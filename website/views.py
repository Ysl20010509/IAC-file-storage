from flask import Blueprint, render_template, request, flash, jsonify, send_file, redirect, url_for
from flask_login import login_required, current_user
from .models import Upload
from . import db
from io import BytesIO
import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    files = Upload.query.all()
    return render_template("home.html", user=current_user, files=files)

@views.route('/upload', methods=['POST'])
@login_required
def upload():
    files = request.files.getlist('file')
    for file in files:
        if file:
            #TODO: Set a proper folder_id
            upload = Upload(filename=file.filename, data=file.read(), user_id=current_user.id, folder_id=0)
            db.session.add(upload)
            db.session.commit()
            flash(file.filename + ' uploaded!', category="success")
        else:
            flash("Please select a file", category="error")
    return redirect(url_for('views.home'))


@views.route('/myfiles', methods=['GET', 'POST'])
@login_required
def myfiles():
    files = Upload.query.filter_by(user_id=current_user.id)
    return render_template("myfiles.html", user=current_user, files=files)


@views.route('/download', methods=['POST'])
def download():  
    file = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    fileId = file['fileId']
    filename = file['filename']
    print(fileId)
    upload = Upload.query.filter_by(id=fileId).first()
    print(1)
    response = send_file(BytesIO(upload.data), download_name=upload.filename, as_attachment=True)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
    
@views.route('/delete', methods=['POST'])
def delete():
    file = json.loads(request.data)

    filename = file['filename']

    fileId = file['fileId']

    user_id = current_user.id
    upload = Upload.query.filter_by(id=fileId).first()
    if upload.user_id == user_id:
        print(1)
        db.session.delete(upload)
        db.session.commit()
        print(2)
        flash(filename + ' deleted', category="success")
        print(3)
    #This has problem
    return redirect(url_for('views.myfiles'))

@views.route('/download/<upload_id>')
def download_file(upload_id):
    upload = Upload.query.filter_by(id=upload_id).first()
    return send_file(BytesIO(upload.data), download_name=upload.filename, as_attachment=True)