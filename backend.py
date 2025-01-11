import sqlite3
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Configuração para liberar CORS de qualquer origem
CORS(app, resources={r"/*": {"origins": "*"}})

# Função para conectar ao banco SQLite
def get_db_connection():
    conn = sqlite3.connect("infractions.db")  # Caminho para o arquivo do banco SQLite
    conn.row_factory = sqlite3.Row  # Acessa os resultados como dicionários
    return conn

# Função para inserir uma infração
@app.route("/infractions", methods=["POST"])
def add_infraction():
    # Verifica se o conteúdo da requisição é JSON
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Obtém os dados enviados
    data = request.get_json()

    # Valida se os campos obrigatórios estão presentes
    plate = data.get("plate")
    speed = data.get("speed")
    timestamp = data.get("timestamp")

    if not plate or not speed or not timestamp:
        return jsonify({"error": "Missing required fields: plate, speed, timestamp"}), 400

    # Conexão ao banco de dados e inserção
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO infractions (plate, speed, timestamp) VALUES (?, ?, ?)",
            (plate, speed, timestamp),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

    conn.close()
    return jsonify({"message": "Infraction added successfully"}), 201

# Rota para listar todas as infrações
@app.route('/infractions', methods=['GET'])
def get_all_infractions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, plate, speed, timestamp FROM infractions ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    # Converte os resultados da consulta para JSON
    data = [
        {
            "id": row[0],
            "plate": row[1],
            "speed": row[2],
            "timestamp": row[3],
        }
        for row in rows
    ]
    return jsonify(data), 200

# Rota para consultar infrações por placa
@app.route('/infractions/<plate>', methods=['GET'])
def get_infractions_by_plate(plate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, plate, speed, timestamp FROM infractions WHERE plate = ?", (plate,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({'message': 'Nenhuma infração encontrada para esta placa.'}), 404

    data = [
        {
            "id": row[0],
            "plate": row[1],
            "speed": row[2],
            "timestamp": row[3],
        }
        for row in rows
    ]
    return jsonify(data), 200

# Rota para excluir infração
@app.route('/infractions/<int:id>', methods=['DELETE'])
def delete_infraction(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM infractions WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({'error': 'Infração não encontrada!'}), 404

    cursor.execute("DELETE FROM infractions WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Infração excluída com sucesso!'}), 200

# Inicializar o banco de dados se necessário (criação de tabela)
def setup_database():
    conn = sqlite3.connect("infractions.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS infractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT NOT NULL,
            speed REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Iniciar servidor
if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
