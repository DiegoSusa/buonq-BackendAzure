from flask import Flask, request, jsonify
from database import conectar
from datetime import datetime
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "API BuonQ funcionando", "status": "ok"})

@app.route("/reservar", methods=["POST"])
def reservar():
    try:
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        personas_raw = request.form["personas"]
        personas = int(personas_raw.replace("+", "").split()[0])
        fecha = request.form["fecha"]
        hora_raw = request.form["hora"]
        hora = datetime.strptime(hora_raw, "%I:%M %p").time()
        comentarios = request.form["comentarios"]

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO reservas
            (nombre, telefono, email, personas, fecha, hora, comentarios)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, telefono, email, personas, fecha, hora, comentarios))

        conexion.commit()
        cursor.close()
        conexion.close()

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)