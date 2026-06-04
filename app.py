import os
from datetime import datetime
from flask import Flask, request, jsonify
from database import conectar

app = Flask(__name__)

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
        # En caso de error, devolvemos el mensaje y un código de estado 400
        return jsonify({"success": False, "error": str(e)}), 400

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=puerto)
