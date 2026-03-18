from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic, json, os
app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY",""))

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/health")
def health():
    return jsonify({"status":"ok","app":"BioHuerta v4.0"})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        if not messages:
            return jsonify({"error": "No messages"}), 400
        r = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1000,
            system=data.get("system","Sos un experto en huerta organica argentina."),
            messages=messages
        )
        return jsonify({"reply": r.content[0].text})
    except anthropic.AuthenticationError:
        return jsonify({"error": "API key invalida o no configurada en Render"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analizar-planta", methods=["POST"])
def analizar_planta():
    try:
        data = request.json or {}
        img = data.get("image","")
        mt = data.get("media_type","image/jpeg")
        if not img:
            return jsonify({"error": "No se recibio imagen"}), 400
        r = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1200,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":mt,"data":img}},
                {"type":"text","text":'Analiza esta planta de huerta y responde SOLO con un objeto JSON valido, sin markdown, sin explicaciones extra. Formato exacto: {"planta":"nombre comun","confianza":"alta/media/baja","estado_general":"descripcion breve del estado","carencias":[{"nutriente":"nombre","sintoma":"descripcion","solucion":"accion concreta"}],"excesos":[{"nutriente":"nombre","sintoma":"descripcion","solucion":"accion concreta"}],"recomendacion_principal":"texto","abono_sugerido":"nombre del abono"}'}
            ]}]
        )
        texto = r.content[0].text.strip()
        # Limpiar posibles markdown fences
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
            texto = texto.strip()
        resultado = json.loads(texto)
        return jsonify(resultado)
    except anthropic.AuthenticationError:
        return jsonify({"error": "API key invalida. Configurar ANTHROPIC_API_KEY en Render > Environment"}), 401
    except json.JSONDecodeError as e:
        return jsonify({"error": "La IA no devolvio JSON valido: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
