from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

import os
import subprocess
import zipfile
import shortuuid
import psycopg2

######################################################################
## Configs
PORT = int(os.environ.get("PORT", 5001))
DATABASE_URL = os.environ.get("DATABASE_URL")

ALLOWED_EXTENSIONS = set(['zip'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['WS_FOLDER'] = './workspaces'

######################################################################
## Helpers
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def dump_all(conn):
    cur = conn.cursor()
    
    cur.execute("SELECT id, count, created_at as when FROM Counts")
    
    for iden, count, when in cur.fetchall() :
        print iden, count, when

def insert_count(conn, iden, count):
    cur = conn.cursor()
    cur.execute("""
         INSERT INTO counts(id, count, created_at) 
         VALUES (%s, %s, NOW()) 
         ON CONFLICT (id) DO UPDATE
         SET count = %s, created_at=NOW()
         WHERE counts.id = %s
    """ % (iden, count, count, iden))
    conn.commit()
                
######################################################################
## Initialize

conn = psycopg2.connect(DATABASE_URL)
dump_all(conn)

# make sure folders exists
for d in [app.config['UPLOAD_FOLDER'], app.config['WS_FOLDER']]:
    if not os.path.exists(d):
        os.makedirs(d)

        
######################################################################
## Routes
@app.route("/upload/<iden>", methods=['GET', 'POST'])
def upload_handler(iden):

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

    # Find todo references
    s = subprocess.Popen(("grep", "-r", "-n", "TODO", "."), stdout = subprocess.PIPE, cwd=toFolder)
    out, err = s.communicate()

    count = out.count('\n')

    # Save to DB
    print(iden, count)
    print()
    insert_count(conn, iden, count)

    print count
    print out
    
    return str(count) + '\n' + out

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=True)
