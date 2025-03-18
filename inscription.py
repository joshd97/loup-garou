import uuid
import sqlite3
import bcrypt
from flask import Flask, request, jsonify

app = Flask(__name__)

# Connexion à la base de données et création des tables si elles n'existent pas
def init_db():
    conn = sqlite3.connect("game.db")
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Table des joueurs (si elle n'existe pas déjà)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            login TEXT UNIQUE,
            role TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Fonction pour hasher un mot de passe
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

# Fonction pour enregistrer un joueur
@app.route('/api/v1/register', methods=['POST'])
def register():
    data = request.get_json()

    try:
        username = data['username']
        password = data['password']
        
        # Vérifier que le nom d'utilisateur est valide
        if not (3 <= len(username) <= 20 and username.isalnum()):
            return jsonify({"error": "Nom d'utilisateur invalide"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères"}), 400

        # Hasher le mot de passe
        hashed_password = hash_password(password)

        # Enregistrer l'utilisateur en base de données
        conn = sqlite3.connect("game.db")
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (id, username, password) VALUES (?, ?, ?)',
            (str(uuid.uuid4()), username, hashed_password)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Inscription réussie"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Nom d'utilisateur déjà utilisé"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
