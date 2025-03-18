from flask import Flask, request, jsonify
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import sqlite3
import logging
import uuid
import traceback
import os

# Configuration avancée du logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Handler console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Handler fichier log
file_handler = logging.FileHandler('log.txt')
file_handler.setLevel(logging.INFO)

# Format commun
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Ajout des handlers au logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

app = Flask(__name__)

# Types et modèles
class Role(Enum):
    LOUP = "loup"
    VILLAGEOIS = "villageois"

class PlayerStatus(Enum):
    ALIVE = "vivant"
    DEAD = "mort"

@dataclass
class Position:
    x: int
    y: int

@dataclass
class Player:
    id: str
    login: str
    role: Role
    position: Position
    status: PlayerStatus

# Gestionnaire de base de données
class GameDB:
    def __init__(self, db_name='game.db'):
        self.db_name = db_name
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                login TEXT UNIQUE,
                role TEXT,
                x INTEGER,
                y INTEGER,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_player(self, player_id, login, role, x, y, status):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO players (id, login, role, x, y, status) VALUES (?, ?, ?, ?, ?, ?)',
            (player_id, login, role, x, y, status)
        )
        conn.commit()
        conn.close()

    def update_position(self, player_id, x, y):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE players SET x = ?, y = ? WHERE id = ?', (x, y, player_id))
        conn.commit()
        conn.close()

    def get_player(self, player_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        conn.close()
        return player

db = GameDB()

def generate_initial_position() -> Tuple[int, int]:
    return (0, 0)

def generate_player_id() -> str:
    return str(uuid.uuid4())

# Gestion globale des erreurs
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Erreur : {traceback.format_exc()}")
    return jsonify({"error": str(e)}), 500

# Routes
@app.route('/')
def home():
    return 'Bienvenue sur le serveur Loup Garou!'

@app.route('/api/v1/inscription', methods=['POST'])
def inscription():
    data = request.get_json()
    login = data.get('login')
    role = data.get('role')

    if not login or not (3 <= len(login) <= 20) or not login.isalnum():
        return jsonify({"error": "Login invalide"}), 400

    if role not in [r.value for r in Role]:
        return jsonify({"error": "Rôle invalide"}), 400

    player_id = generate_player_id()
    position = generate_initial_position()

    try:
        db.add_player(player_id, login, role, position[0], position[1], PlayerStatus.ALIVE.value)
        logger.info(f"Nouveau joueur inscrit : {login}")
        return jsonify({"player_id": player_id, "login": login, "role": role, "x": position[0], "y": position[1]}), 200

    except sqlite3.IntegrityError:
        return jsonify({"error": "Login déjà utilisé"}), 409

@app.route('/api/v1/deplacement/<player_id>', methods=['POST'])
def deplacement(player_id):
    data = request.get_json()
    new_x = data.get('x')
    new_y = data.get('y')

    if new_x is None or new_y is None:
        return jsonify({"error": "Coordonnées manquantes"}), 400

    db.update_position(player_id, new_x, new_y)
    logger.info(f"Déplacement joueur {player_id} vers ({new_x}, {new_y})")
    return jsonify({"success": True, "position": {"x": new_x, "y": new_y}}), 200

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        logger.info("Démarrage du serveur Flask...")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
