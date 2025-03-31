import webbrowser
from threading import Timer
from flask import render_template
from scolarite_app import app
import os  # Import pour vérifier le mode de rechargement

@app.route('/')
def main_home():
    return render_template('index.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

def browser():
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Vérification pour éviter l'exécution multiple en mode debug
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        Timer(1, browser).start()
    app.run(host='0.0.0.0', port=5000, debug=True)