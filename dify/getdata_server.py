"""This script sets up a Flask server that listens for POST requests on the /upload endpoint.
When a request is received, it expects a JSON payload containing a filename and data.
接收dify的json数据，保存为文件 (dify:優化小說內容流程).
"""  # noqa: D205
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        jobj = request.get_json()
        filename = jobj.get('filename')
        # if filename is exists, add a number to the filename
        if filename:
            i = 1
            while os.path.exists(filename):
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{i}{ext}"
                i += 1
        data = jobj.get('data')
        
        if not filename or not data:
            return jsonify({'error': 'Missing filename or data'}), 400
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        
        return jsonify({'message': 'File saved successfully', 'filename': filename}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9125, debug=True)
# To run the server, use the command: python getdata_server.py