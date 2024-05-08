from flask import Blueprint, render_template, request, flash, jsonify, send_file, redirect, url_for, send_from_directory, session, abort
from flask_login import login_required, current_user
from .models import Upload, Folder
from . import db
from io import BytesIO
import json, base64, mimetypes
from . import PATH, FOLDER_ID, PARENTS_ID, PARENTS_PATH
from sqlalchemy import and_, or_, not_

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    
    folders = Folder.query.filter_by(parent_id=session['FOLDER_ID']).all()
    files = Upload.query.filter_by(folder_id=session['FOLDER_ID']).all()
    return render_template("home.html", user=current_user, files=files, folders=folders, path=session['PATH'])

@views.route('/upload', methods=['POST'])
@login_required
def upload():
    files = request.files.getlist('file')
    for file in files:
        if file:
            #TODO: Set a proper folder_id
            upload = Upload(filename=file.filename, data=file.read(), user_id=current_user.id, folder_id=session['FOLDER_ID'])
            db.session.add(upload)
            db.session.commit()
            flash(file.filename + ' uploaded!', category="success")
        else:
            flash("Please select a file", category="error")
    return redirect(url_for('views.home'))

@views.route('/newfolder', methods=['POST'])
@login_required
def newfolder():
    name = request.form['folder']
    if (name==""):
        flash("Please name your folder first", category="error")
        return redirect(url_for("views.home"))
    exist_folder = Folder.query.filter_by(foldername=name, parent_id=session['FOLDER_ID']).first()
    if exist_folder != None:
        flash(name + ' already exists!', category="error")
    else:
        new_folder = Folder(path=session['PATH']+'/'+name, foldername=name, parent_id=session['FOLDER_ID'], user_id=current_user.id)
        db.session.add(new_folder)
        db.session.commit()
        flash(name + " created!", category="success")    
    return redirect(url_for('views.home'))


@views.route('/myfiles', methods=['GET', 'POST'])
@login_required
def myfiles():
    folders = Folder.query.filter_by(parent_id=session['FOLDER_ID']).all()
    files = Upload.query.filter_by(user_id=current_user.id, folder_id=session['FOLDER_ID']).all()
    return render_template("myfiles.html", user=current_user, files=files, folders=folders, path=session['PATH'])


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

# @views.route('/enterfolder', methods=['POST'])
# def enterfolder():
#     global PATH, FOLDER_ID, PARENTS_ID, PARENTS_PATH
    
#     param = json.loads(request.data)
#     folderId = param['folderId']
#     folderName = param['folderName']
#     if folderName == "..":
#         if len(PARENTS_ID) > 0:
#             FOLDER_ID = PARENTS_ID.pop()
#             PATH = PARENTS_PATH.pop()
#         return redirect(url_for('views.home'))
#     folder = Folder.query.filter_by(id=folderId, foldername=folderName).first()
#     if folder is not None:
#         if folder.itar and not current_user.itar_permission:
#             flash("Access denied: Folder requires ITAR permission", category='error')
#             return redirect(url_for('views.home'))
#         PARENTS_ID.append(FOLDER_ID)
#         PARENTS_PATH.append(PATH)
#         if FOLDER_ID == 0:
#             PATH += folderName
#         else:
#             PATH = PATH + '/' + folderName
#         FOLDER_ID = folderId
#     else:
#         flash("Folder not exist", category="error")

#     return redirect(url_for('views.home'))

@views.route('/enterfolder', methods=['POST'])
def enterfolder():
    param = json.loads(request.data) 
    folderId = param['folderId']
    folderName = param['folderName']

    if 'FOLDER_ID' not in session:
        session['FOLDER_ID'] = 0
        session['PATH'] = '/'
        session['PARENTS_ID'] = []
        session['PARENTS_PATH'] = []

    if folderName == "..":
        # Navigate to parent folder
        if session['PARENTS_ID']:
            session['FOLDER_ID'] = session['PARENTS_ID'].pop()
            session['PATH'] = session['PARENTS_PATH'].pop()
        session.modified = True 
        return redirect(url_for('views.home'))

    folder = Folder.query.filter_by(id=folderId, foldername=folderName).first()
    if folder is not None:
        if folder.itar and not current_user.itar_permission:
            flash("Access denied: Folder requires ITAR permission", category='error')
            return redirect(url_for('views.home'))
        session['PARENTS_ID'].append(session['FOLDER_ID'])
        session['PARENTS_PATH'].append(session['PATH'])
        if session['FOLDER_ID'] == 0:
            session['PATH'] += folderName
        else:
            session['PATH'] = session['PATH'] + '/' + folderName
        session['FOLDER_ID'] = folderId
        session.modified = True
    else:
        flash("Folder not exist", category="error")

    return redirect(url_for('views.home'))



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



@views.route('/preview/<file_id>', methods=['GET'])
def preview(file_id):
    upload = Upload.query.filter_by(id=file_id).first()
    if not upload:
        # Use Flask's abort to send a 404 HTTP response
        return jsonify({'error': 'File not found'}), 404

    # Debugging print statement - remove or comment out for production
    print(upload.id)
    
    content_type, _ = mimetypes.guess_type(upload.filename)
    if content_type:
        filename = upload.filename
        file_data_base64 = base64.b64encode(upload.data).decode('utf-8')

        if content_type.startswith('image'):
            return render_template('image_preview.html', file_data_base64=file_data_base64, filename=filename, content_type=content_type)
        elif content_type.startswith('application/pdf'):
            return render_template('pdf_preview.html', file_data_base64=file_data_base64, filename=filename)
        else:
            return jsonify({'error': 'File type not supported for preview. Please download to view.'}), 415
    else:
        return jsonify({'error': 'Unable to determine file type. Please download to view.'}), 415

    return redirect(url_for('views.home'))

@views.route('/deletefolder', methods=['POST'])
def deletefolder():
    param = json.loads(request.data)
    foldername = param['foldername']
    folderId = param['folderId']
    folder = Folder.query.filter_by(id=folderId).first()
    if folder != None:
        file = Upload.query.filter_by(folder_id=folderId).first()
        if file == None:
            db.session.delete(folder)
            db.session.commit()
            flash(foldername + ' deleted', category='success')
            #return ('0')
        else:
            flash(foldername + ' is not empty, please delete all the files in it first', category='error')
            #return ('-1')
    else:
        flash(foldername + " doesn't exist!", category='error')
        #return ('-2')
    
@views.route('/markItar', methods=["POST"])
def markItar():
    param = json.loads(request.data)
    foldername = param['foldername']
    folderId = param['folderId']
    folder = Folder.query.filter_by(id=folderId).first()
    if folder != None:
        folder.itar = True  # Set the itar attribute to True
        db.session.commit()
        flash("Folder marked as ITAR", category="success")
    else:
        flash(foldername + " doesn't exist!", category='error')
        return ('-2')

@views.route('/unmarkItar', methods=["POST"])
def unmarkItar():
    param = json.loads(request.data)
    foldername = param['foldername']
    folderId = param['folderId']
    folder = Folder.query.filter_by(id=folderId).first()
    if folder != None:
        folder.itar = False  # Set the itar attribute to False
        db.session.commit()
        flash("Folder ITAR unmarked", category="success")
    else:
        flash(foldername + " doesn't exist!", category='error')
        return ('-2')
    
@views.route('/download/<upload_id>')
def download_file(upload_id):
    upload = Upload.query.filter_by(id=upload_id).first()
    return send_file(BytesIO(upload.data), download_name=upload.filename, as_attachment=True)

@views.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    file_results = db.session.query(Upload, Folder).join(Folder, Upload.folder_id == Folder.id).filter(Upload.filename.like(f'%{query}%')).all()
    
    results = [{'filename': upload.filename, 'foldername': folder.foldername, 'folderid': folder.id, 'path': folder.path} for upload, folder in file_results]
    
    return render_template("search_results.html", user=current_user, results=results)


