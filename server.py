from flask import Flask, request, jsonify
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
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

# Stockage en mémoire des joueurs
players_db = {}

def generate_initial_position() -> Position:
    return Position(0, 0)

def generate_player_id() -> str:
    return str(uuid.uuid4())

# Fonctions de gestion des joueurs
def add_player(login: str, role: str) -> Player:
    player_id = generate_player_id()
    position = generate_initial_position()
    
    player = Player(
        id=player_id,
        login=login,
        role=role,
        position=position,
        status=PlayerStatus.ALIVE.value
    )
    
    players_db[player_id] = player
    return player

def update_position(player_id: str, x: int, y: int) -> Optional[Player]:
    if player_id in players_db:
        players_db[player_id].position.x = x
        players_db[player_id].position.y = y
        return players_db[player_id]
    return None

def get_player(player_id: str) -> Optional[Player]:
    return players_db.get(player_id)

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

    # Vérifier si le login est déjà utilisé
    if any(player.login == login for player in players_db.values()):
        return jsonify({"error": "Login déjà utilisé"}), 409

    player = add_player(login, role)
    logger.info(f"Nouveau joueur inscrit : {login}")
    
    return jsonify({
        "player_id": player.id,
        "login": player.login,
        "role": player.role,
        "x": player.position.x,
        "y": player.position.y
    }), 200

@app.route('/api/v1/deplacement/<player_id>', methods=['POST'])
def deplacement(player_id):
    data = request.get_json()
    new_x = data.get('x')
    new_y = data.get('y')

    if new_x is None or new_y is None:
        return jsonify({"error": "Coordonnées manquantes"}), 400

    updated_player = update_position(player_id, new_x, new_y)
    
    if not updated_player:
        return jsonify({"error": "Joueur non trouvé"}), 404
        
    logger.info(f"Déplacement joueur {player_id} vers ({new_x}, {new_y})")
    return jsonify({"success": True, "position": {"x": new_x, "y": new_y}}), 200

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        logger.info("Démarrage du serveur Flask...")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)