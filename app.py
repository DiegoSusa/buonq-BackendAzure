import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import conectar

app = Flask(__name__)
CORS(app)  # Permite peticiones desde cualquier frontend

# Para que Azure App Service (Gunicorn) detecte la aplicación correctamente
application = app

@app.route("/")
def home():
    return jsonify({"message": "API BuonQ funcionando", "status": "ok"})

@app.route("/reservar", methods=["POST"])
def reservar():
    conexion = None
    cursor = None
    try:
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        
        personas_raw = request.form["personas"]
        personas = int(personas_raw.replace("+", "").split()[0])
        
        fecha = request.form["fecha"]
        
        hora_raw = request.form["hora"]
        hora_obj = datetime.strptime(hora_raw, "%I:%M %p").time()
        hora_sql = hora_obj.strftime("%H:%M:%S")
        
        comentarios = request.form["comentarios"]

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
        # Verificar si es error por duplicado (UNIQUE constraint)
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