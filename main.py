from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

import os
import subprocess
import zipfile
import shortuuid

######################################################################
## Configs
ALLOWED_EXTENSIONS = set(['zip'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['WS_FOLDER'] = './workspaces'

######################################################################
## Helpers
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

######################################################################
## Routes
@app.route("/", methods=['GET', 'POST'])
def index():

    # TODO for debugging, remove later
    if request.method != 'POST':
        return """
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file>
        <input type=submit value=Upload>
        </form>
        <p>%s</p>
        """ % "<br>".join(os.listdir(app.config['UPLOAD_FOLDER'],))

    file = request.files['file']

    if not file:
        return "No file attached"
    if not allowed_file(file.filename):
        return "File Extension not supported"

    # use uuid to avoid name colisions
    filename = shortuuid.uuid()
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Unzip
    zip_ref = zipfile.ZipFile(app.config['UPLOAD_FOLDER'] + '/' + filename, 'r')
    toFolder = app.config['WS_FOLDER'] + '/' + filename
    zip_ref.extractall(toFolder)
    zip_ref.close()

    # Find TODO references
    s = subprocess.Popen(("grep", "-r", "TODO", "."), stdout = subprocess.PIPE, cwd=toFolder)
    out, err = s.communicate()
    
    print out
    return out
            
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
