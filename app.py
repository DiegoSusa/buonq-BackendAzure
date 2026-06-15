import os
import re
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from database import conectar
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
CORS(app)

application = app

# ==========================================
# CONFIGURACIÓN DE EMAIL
# ==========================================

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = "buonqrestaurant@gmail.com"


def enviar_correo_confirmacion(destinatario, nombre, fecha, hora, personas):
    try:
        if not SENDGRID_API_KEY:
            print("SENDGRID_API_KEY no configurada")
            return False

        html_content = render_template(
            "email_confirmacion.html",
            nombre=nombre,
            fecha=fecha,
            hora=hora,
            personas=personas
        )

        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=destinatario,
            subject="Confirmación de reserva - BuonQ",
            html_content=html_content
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print(
            f"Correo enviado a {destinatario} - Status: {response.status_code}"
        )

        return True

    except Exception as e:
        print("Error enviando correo:", str(e))
        return False


@app.route("/")
def home():
    return jsonify({
        "message": "API BuonQ funcionando",
        "status": "ok"
    })


@app.route("/reservar", methods=["POST"])
def reservar():

    conexion = None
    cursor = None

    try:

        # ==========================================
        # OBTENER DATOS DEL FORMULARIO
        # ==========================================

        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        personas_raw = request.form.get("personas", "").strip()
        fecha = request.form.get("fecha", "").strip()
        hora_raw = request.form.get("hora", "").strip()
        comentarios = request.form.get("comentarios", "").strip()

        # ==========================================
        # VALIDACIONES DE CAMPOS OBLIGATORIOS
        # ==========================================

        if not nombre:
            return jsonify({
                "success": False,
                "error": "El nombre es obligatorio"
            }), 400

        if not telefono:
            return jsonify({
                "success": False,
                "error": "El teléfono es obligatorio"
            }), 400

        if not email:
            return jsonify({
                "success": False,
                "error": "El email es obligatorio"
            }), 400

        if not fecha:
            return jsonify({
                "success": False,
                "error": "La fecha es obligatoria"
            }), 400

        if not hora_raw:
            return jsonify({
                "success": False,
                "error": "La hora es obligatoria"
            }), 400

        if not personas_raw:
            return jsonify({
                "success": False,
                "error": "Debes seleccionar el número de personas"
            }), 400

        # ==========================================
        # VALIDACIÓN DE EMAIL
        # ==========================================

        if "@" not in email or "." not in email:
            return jsonify({
                "success": False,
                "error": "Ingresa un email válido (ejemplo: correo@dominio.com)"
            }), 400

        # ==========================================
        # VALIDACIÓN DE TELÉFONO
        # ==========================================

        telefono_limpio = re.sub(r"[^\d+]", "", telefono)

        if len(telefono_limpio) < 7:
            return jsonify({
                "success": False,
                "error": "El teléfono debe tener al menos 7 dígitos"
            }), 400

        # ==========================================
        # VALIDAR PERSONAS
        # ==========================================

        try:
            personas = int(
                personas_raw.replace("+", "").split()[0]
            )

        except (ValueError, IndexError):
            return jsonify({
                "success": False,
                "error": "Cantidad de personas inválida"
            }), 400

        # ==========================================
        # VALIDAR FECHA
        # ==========================================

        try:
            fecha_obj = datetime.strptime(
                fecha,
                "%Y-%m-%d"
            )

            fecha_formateada = fecha_obj.strftime(
                "%d/%m/%Y"
            )

        except ValueError:
            return jsonify({
                "success": False,
                "error": "Formato de fecha inválido"
            }), 400

        # ==========================================
        # VALIDAR HORA
        # ==========================================

        try:
            hora_obj = datetime.strptime(
                hora_raw,
                "%I:%M %p"
            ).time()

            hora_sql = hora_obj.strftime("%H:%M:%S")

            hora_formateada = hora_obj.strftime(
                "%I:%M %p"
            ).lstrip("0")

        except ValueError:
            return jsonify({
                "success": False,
                "error": "Formato de hora inválido"
            }), 400

        # ==========================================
        # INSERTAR EN BASE DE DATOS
        # ==========================================

        conexion = conectar()
        cursor = conexion.cursor()

        sql_query = """
            INSERT INTO reservas
            (
                nombre,
                telefono,
                email,
                personas,
                fecha,
                hora,
                comentarios
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(
            sql_query,
            (
                nombre,
                telefono,
                email,
                personas,
                fecha,
                hora_sql,
                comentarios
            )
        )

        conexion.commit()

        # ==========================================
        # ENVIAR CORREO
        # ==========================================

        correo_enviado = enviar_correo_confirmacion(
            destinatario=email,
            nombre=nombre,
            fecha=fecha_formateada,
            hora=hora_formateada,
            personas=personas
        )

        mensaje = "Reserva creada con éxito"

        if correo_enviado:
            mensaje += " - Correo de confirmación enviado"

        else:
            mensaje += " - No se pudo enviar el correo"

        return jsonify({
            "success": True,
            "message": mensaje,
            "email_sent": correo_enviado
        }), 201

    except Exception as e:

        error_msg = str(e)

        print("ERROR BD:", error_msg)

        if (
            "UNIQUE" in error_msg
            or "duplicate" in error_msg.lower()
            or "violation" in error_msg.lower()
        ):
            return jsonify({
                "success": False,
                "error": (
                    "Ya existe una reserva para esta fecha y hora. Por favor elige otro horario."
                )
            }), 400

        return jsonify({
            "success": False,
            "error": (
                "Ocurrió un error al procesar la reserva. Intenta nuevamente más tarde."
            )
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=puerto)