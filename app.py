import os
import json
import subprocess
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/login', methods=['POST', 'GET'])
def login():
    try:
        # Ejecutar el comando npx notebooklm-sdk login
        # shell=True permite encontrar 'npx' en Windows de forma confiable
        result = subprocess.run(['npx', 'notebooklm-sdk', 'login'], capture_output=True, text=True, shell=True)
        
        # La ruta donde el SDK guarda el session.json por defecto es en el home del usuario
        session_file = os.path.expanduser(r'~/.notebooklm/session.json')
        
        if os.path.exists(session_file):
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            return jsonify({
                'success': True,
                'message': 'Login completado',
                'session': session_data,
                'cli_output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': 'El comando se ejecutó pero no se encontró el archivo session.json',
                'cli_output': result.stdout,
                'cli_error': result.stderr
            }), 500

    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
