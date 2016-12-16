from flask import Flask, request, redirect, url_for, Response
from werkzeug import secure_filename

import os
import subprocess
import zipfile
import shortuuid
import psycopg2
import requests

######################################################################
## Configs

PORT = int(os.environ.get('PORT', 5001))
DATABASE_URL = os.environ.get('DATABASE_URL')

ALLOWED_EXTENSIONS = set(['zip'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['WS_FOLDER'] = './workspaces'

######################################################################
## Helpers

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

###
# Database Helpers

def get_all_counts(conn):
    cur = conn.cursor()
    cur.execute('SELECT id, count, created_at as when FROM Counts')
    
    for iden, count, when in cur.fetchall():
        print iden, count, when

def get_count(conn, iden):
    cur = conn.cursor()
    cur.execute('SELECT count FROM Counts WHERE id = %s' % iden)
    
    return cur.fetchone()[0]

def insert_count(conn, iden, count):
    cur = conn.cursor()
    cur.execute('''
         INSERT INTO counts(id, count, created_at) 
         VALUES (%s, %s, NOW()) 
         ON CONFLICT (id) DO UPDATE
         SET count = %s, created_at=NOW()
         WHERE counts.id = %s
    ''' % (iden, count, count, iden))
    conn.commit()
                
######################################################################
## Initialization

conn = psycopg2.connect(DATABASE_URL)

# make sure folders exists
for d in [app.config['UPLOAD_FOLDER'], app.config['WS_FOLDER']]:
    if not os.path.exists(d):
        os.makedirs(d)
        
######################################################################
## Routes

@app.route('/upload/<iden>', methods=['GET', 'POST'])
def upload_handler(iden):
    """
    Receives code uploads, counts TODO occurences and stores result in database.

    You can trigger this either by using the upload form in the browser or curl:
       curl -F file=@<zipped src folder>.zip http://localhost:5001/upload/<id>
    """

    # Provide upload form for manual builds and debugging
    if request.method == 'GET':
        return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file>
        <input type=submit value=Upload>
        </form>
        <p>%s</p>
        ''' % '<br>'.join(os.listdir(app.config['UPLOAD_FOLDER'],))
    
    file = request.files['file']

    if not file:
        return 'No file attached'
    if not allowed_file(file.filename):
        return 'File Extension not supported'

    # use uuid to avoid name colisions
    filename = shortuuid.uuid()
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Unzip to working directory
    zip_ref = zipfile.ZipFile(app.config['UPLOAD_FOLDER'] + '/' + filename, 'r')
    toFolder = app.config['WS_FOLDER'] + '/' + filename
    zip_ref.extractall(toFolder)
    zip_ref.close()

    # Find todo references
    s = subprocess.Popen(('grep', '-r', '-n', 'TODO', '.'), stdout = subprocess.PIPE, cwd=toFolder)
    out, err = s.communicate()

    # Count occurrences
    count = out.count('\n')

    # Save to DB
    insert_count(conn, iden, count)

    return str(count) + '\n' + out

@app.route('/badges/id/<iden>.png')
def get_badge_handler(iden):
    """Generates badge from TODO count of given id."""
    count = get_count(conn, iden)

    # Generate badge via shields.io
    url = 'https://img.shields.io/badge/TODOs-%s-brightgreen.svg?style=flat' % count
    img = requests.get(url, stream=True, params = request.args)

    # Pipe response from shields.io to our request response
    headers = {'Content-Type': 'image/svg+xml;charset=utf-8'}
    return Response(img, headers=headers)

@app.route('/static/<path:path>')
def serve_static(path):
    """Serves static files, used to provide upload.sh script."""
    return send_from_directory('static', path)

######################################################################
## Main
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
