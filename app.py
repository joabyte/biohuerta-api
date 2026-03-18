from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic
import base64
import json
import os

app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        system_prompt = data.get("system", "Sos un experto en huerta organica argentina.")
        messages = data.get("messages", [])
        if not messages:
            return jsonify({"error": "No messages"}), 400
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        return jsonify({"reply": response.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analizar-planta", methods=["POST"])
def analizar_planta():
    try:
        data = request.json
        image_b64 = data.get("image")
        media_type = data.get("media_type", "image/jpeg")
        if not image_b64:
            return jsonify({"error": "No image provided"}), 400
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1200,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                    {"type": "text", "text": "Analiza esta imagen de una planta y responde SOLO con un JSON valido (sin markdown) con esta estructura: {\"planta\": \"nombre comun\", \"confianza\": \"alta/media/baja\", \"estado_general\": \"descripcion breve\", \"carencias\": [{\"nutriente\": \"nombre\", \"sintoma\": \"desc\", \"solucion\": \"como corregirlo organicamente\"}], \"excesos\": [{\"nutriente\": \"nombre\", \"sintoma\": \"desc\", \"solucion\": \"como corregirlo\"}], \"recomendacion_principal\": \"consejo urgente en 1 oracion\", \"abono_sugerido\": \"abono organico casero recomendado\"}. Si no hay carencias ni excesos, devuelve listas vacias."}
                ]
            }]
        )
        texto = response.content[0].text.strip()
        resultado = json.loads(texto)
        return jsonify(resultado)
    except json.JSONDecodeError:
        return jsonify({"error": "No se pudo parsear respuesta de la IA"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "BioHuerta v4.0"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
