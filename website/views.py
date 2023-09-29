from flask import Blueprint, render_template, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from .models import Upload
from . import db
from io import BytesIO
import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        file = request.files['file']
        if file:
            upload = Upload(filename=file.filename, data=file.read(), user_id=current_user.id)
            db.session.add(upload)
            db.session.commit()
            flash('File uploaded!', category="success")
        else:
            flash("Please select a file")

    files = Upload.query.all()
    return render_template("home.html", user=current_user, files=files)

@views.route('/myfiles', methods=['GET', 'POST'])
@login_required
def myfiles():
    files = Upload.query.filter_by(user_id=current_user.id)
    return render_template("home.html", user=current_user, files=files)


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
    

@views.route('/download/<upload_id>')
def download_file(upload_id):
    upload = Upload.query.filter_by(id=upload_id).first()
    return send_file(BytesIO(upload.data), download_name=upload.filename, as_attachment=True)