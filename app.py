
from flask import Flask, request
import requests
import os
from datetime import datetime, time

app = Flask(__name__)

# --- CONFIGURACIÓN ---
TOKEN = "EAARYZBHVD4ZBgBQhwSlPCWa3OIPnHlYOmKzfjLSRn6jTWJOtRNUoWTWCgqSnKZCNxJZAuVuUeNFk6zg87ee5b8QZCZCFPGOdMEqToaZCfkOBQ3Q46SDIkwvRfPZAZB4pB6PLUBfP4ZCXwVzIdg19VN7DgZCYA2gY0obIuow3R5ED0lLb6n5ZBbvfrxZBv6zZBAN4NfQ0MmZAX1ZAZCyUKwxDZAoAwFrjuMjCVFDVFRViSZAtMMe9hmZBZBBpLM7Dy2baXmQS5YQ3KfgdaXDOeyah7842nlySKBZADTQpkS"
PHONE_ID = "1011965838664369"
ADMIN_NUMBERS = ["34642011691", "34631324307", "34633102892"]
MENU_LINK = "https://drive.google.com/uc?export=download&id=1_JsjENwjJcCZw3WIXonnuFvxwWFbteeg"
REVIEW_LINK = "https://g.page/r/CeuTmrtoObZAEBM/review"

sessions = {}
shop_open_manual = True

def esta_en_horario():
    ahora = datetime.now().time()
    t1_i, t1_f = time(13, 0), time(17, 0)
    t2_i, t2_f = time(19, 0), time(23, 30)
    return (t1_i <= ahora <= t1_f) or (t2_i <= ahora <= t2_f)

def enviar_texto(numero, mensaje):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": numero, "text": {"body": mensaje}}
    requests.post(url, headers=headers, json=data)

def enviar_menu(numero):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp", "to": numero, "type": "document",
        "document": {"link": MENU_LINK, "filename": "Menu Rehman Doner Kebab.pdf"}
    }
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    token_verificacion = "rehman123"
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == token_verificacion:
        return challenge
    return "Error de token", 403

@app.route("/webhook", methods=["POST"])
def recibir_mensajes():
    global shop_open_manual
    data = request.json
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        usuario = msg["from"]
        texto = msg.get("text", {}).get("body", "").strip().lower()
    except:
        return "ok"

    # Control de administrador (Abrir/Cerrar)
    if usuario in ADMIN_NUMBERS:
        if texto == "cerrar":
            shop_open_manual = False
            enviar_texto(usuario, "🔴 Local CERRADO manualmente.")
            return "ok"
        if texto == "abrir":
            shop_open_manual = True
            enviar_texto(usuario, "🟢 Local ABIERTO.")
            return "ok"

    # Verificación de horario
    if not (shop_open_manual and esta_en_horario()):
        enviar_texto(usuario, "❌ ¡Hola! Ahora estamos cerrados.\nHorario: 13:00-17:00 y 19:00-23:30.")
        return "ok"

    # Flujo del pedido
    if usuario not in sessions:
        sessions[usuario] = {"paso": "DIRECCION"}
        enviar_texto(usuario, "👋 ¡Bienvenido a Rehman Doner Kebab!\n📍 Por favor, dinos tu dirección para el reparto.")
    elif sessions[usuario]["paso"] == "DIRECCION":
        sessions[usuario]["direccion"] = texto
        sessions[usuario]["paso"] = "PEDIDO"
        enviar_menu(usuario)
        enviar_texto(usuario, "📋 Arriba tienes el menú.\n🍽 ¿Qué quieres pedir hoy?")
    elif sessions[usuario]["paso"] == "PEDIDO":
        sessions[usuario]["pedido"] = texto
        sessions[usuario]["paso"] = "PAGO"
        enviar_texto(usuario, "💳 ¿Cómo quieres pagar? (Tarjeta o Efectivo)")
    elif sessions[usuario]["paso"] == "PAGO":
        mensaje_final = (
            f"✅ ¡Pedido recibido!\n"
            f"📍 Dirección: {sessions[usuario]['direccion']}\n"
            f"🍴 Pedido: {sessions[usuario]['pedido']}\n"
            f"💳 Pago: {texto}\n\n"
            f"En 30-40 min lo tienes allí. ¡Gracias por elegir Rehman Doner Kebab! 🌯\n\n"
            f"⭐ Si te ha gustado, déjanos una reseña aquí:\n{REVIEW_LINK}"
        )
        enviar_texto(usuario, mensaje_final)
        del sessions[usuario]

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
