import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import conectar

app = Flask(__name__)
CORS(app)

application = app

@app.route("/")
def home():
    return jsonify({"message": "API BuonQ funcionando", "status": "ok"})

@app.route("/reservar", methods=["POST"])
def reservar():
    conexion = None
    cursor = None
    try:
        # Obtener datos del formulario
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        personas_raw = request.form.get("personas", "").strip()
        fecha = request.form.get("fecha", "").strip()
        hora_raw = request.form.get("hora", "").strip()
        comentarios = request.form.get("comentarios", "").strip()

        # ==========================================
        # VALIDACIONES SOLO PARA CAMPOS QUE ESCRIBE EL USUARIO
        # ==========================================
        if not nombre:
            return jsonify({"success": False, "error": "El nombre es obligatorio"}), 400
        
        if not telefono:
            return jsonify({"success": False, "error": "El teléfono es obligatorio"}), 400
        
        if not email:
            return jsonify({"success": False, "error": "El email es obligatorio"}), 400

        # ==========================================
        # VALIDACIÓN DE FORMATO DE EMAIL
        # ==========================================
        if "@" not in email or "." not in email:
            return jsonify({"success": False, "error": "Ingresa un email válido (ejemplo: correo@dominio.com)"}), 400

        # ==========================================
        # VALIDACIÓN DE TELÉFONO
        # ==========================================
        import re
        telefono_limpio = re.sub(r'[^\d+]', '', telefono)
        if len(telefono_limpio) < 7:
            return jsonify({"success": False, "error": "El teléfono debe tener al menos 7 dígitos"}), 400

        # ==========================================
        # PROCESAR PERSONAS (viene de select, confiable)
        # ==========================================
        personas = int(personas_raw.replace("+", "").split()[0])

        # ==========================================
        # PROCESAR FECHA Y HORA (confiables)
        # ==========================================
        hora_obj = datetime.strptime(hora_raw, "%I:%M %p").time()
        hora_sql = hora_obj.strftime("%H:%M:%S")

        # ==========================================
        # INSERTAR EN BASE DE DATOS
        # ==========================================
        conexion = conectar()
        cursor = conexion.cursor()

        sql_query = """
            INSERT INTO reservas
            (nombre, telefono, email, personas, fecha, hora, comentarios)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(sql_query, (nombre, telefono, email, personas, fecha, hora_sql, comentarios))
        conexion.commit()

        return jsonify({"success": True, "message": "Reserva creada con éxito"}), 201

    except Exception as e:
        error_msg = str(e)
        if "UNIQUE" in error_msg or "duplicate" in error_msg.lower() or "violation" in error_msg.lower():
            return jsonify({
                "success": False, 
                "error": "Ya existe una reserva para esta fecha y hora. Por favor elige otro horario."
            }), 400
        else:
            return jsonify({"success": False, "error": error_msg}), 400

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=puerto)