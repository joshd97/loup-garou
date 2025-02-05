from flask import Flask, request, jsonify
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import sqlite3
import logging
import uuid

app = Flask(__name__)

# Route de la page d'accueil
@app.route('/')
def home():
    return 'Bienvenue sur le serveur Loup Garou!'

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
    def __init__(self):
        self.conn = sqlite3.connect('game.db')
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                login TEXT UNIQUE,
                role TEXT,
                x INTEGER,
                y INTEGER,
                status TEXT
            )
        ''')
        self.conn.commit()

db = GameDB()

# Définir la fonction generate_initial_position
def generate_initial_position() -> Tuple[int, int]:
    # Exemple de génération de position initiale
    return (0, 0)

# Définir la fonction generate_player_id
def generate_player_id() -> str:
    return str(uuid.uuid4())

# Exemple de définition de la variable tour
tour = 1

# Routes API
@app.route('/api/v1/inscription', methods=['POST'])
def inscription():
    data = request.get_json()
    
    try:
        login = data['login']
        role = data['role']
        
        # Validation
        if not 3 <= len(login) <= 20 or not login.isalnum():
            return jsonify({"error": "Login invalide"}), 400
            
        if role not in ["loup", "villageois"]:
            return jsonify({"error": "Rôle invalide"}), 400

        # Générer position initiale et ID
        player_id = generate_player_id()
        position = generate_initial_position()

        # Sauvegarder dans la DB
        db.cursor.execute(
            'INSERT INTO players (id, login, role, x, y, status) VALUES (?, ?, ?, ?, ?, ?)',
            (player_id, login, role, position[0], position[1], PlayerStatus.ALIVE.value)
        )
        db.conn.commit()

        return jsonify({
            "player_id": player_id,
            "login": login,
            "role": role,
            "x": position[0],
            "y": position[1]
        }), 200

    except sqlite3.IntegrityError:
        return jsonify({"error": "Login déjà utilisé"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/deplacement/<player_id>', methods=['POST'])
def deplacement(player_id):
    data = request.get_json()
    try:
        new_x = data['x']
        new_y = data['y']
        tour = data['tour']

        # Vérifier si le déplacement est valide
        if not is_valid_move(player_id, new_x, new_y):
            return jsonify({"error": "Déplacement invalide"}), 400

        # Mettre à jour la position
        db.cursor.execute(
            'UPDATE players SET x = ?, y = ? WHERE id = ?',
            (new_x, new_y, player_id)
        )
        db.conn.commit()

        return jsonify({
            "success": True,
            "position": {"x": new_x, "y": new_y}
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/vision/<player_id>', methods=['GET'])
def get_vision(player_id):
    try:
        # Récupérer le joueur
        db.cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
        player = db.cursor.fetchone()

        if not player:
            return jsonify({"error": "Joueur non trouvé"}), 404

        # Générer la carte selon la vision du joueur
        vision_map = generate_vision_map(player)
        nearby_players = get_nearby_players(player)

        return jsonify({
            "carte": vision_map,
            "joueurs_proches": nearby_players,
            "elimine": player[5] == PlayerStatus.DEAD.value,
            "tour_actuel": get_current_turn(),
            "temps_restant": get_remaining_time()
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fonctions utilitaires
def generate_vision_map(player) -> List[List[str]]:
    # Implémentation de la génération de carte
    pass

def get_nearby_players(player) -> List[Dict]:
    # Implémentation de la détection des joueurs proches
    pass

def is_valid_move(player_id: str, new_x: int, new_y: int) -> bool:
    # Implémentation de la validation du déplacement
    pass

def get_current_turn() -> int:
    # Implémentation du tour actuel
    pass

def get_remaining_time() -> float:
    # Implémentation du temps restant
    pass

def generate_player_id():
    return str(uuid.uuid4())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)