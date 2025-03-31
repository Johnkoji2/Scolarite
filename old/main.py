from flask import render_template  # Ajout de l'importation manquante
from app import app  # Assurez-vous que 'app' est bien défini dans app.py

@app.route('/')
def main_home():  # Renommé pour éviter le conflit
    return render_template('index.html')  # Affiche le fichier index.html

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404  # Affiche le fichier 404.html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)