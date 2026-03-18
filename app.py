from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic, base64, json, os
app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
@app.route("/")
def index(): return send_from_directory(".", "index.html")
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        if not messages: return jsonify({"error": "No messages"}), 400
        r = client.messages.create(model="claude-opus-4-5", max_tokens=1000,
            system=data.get("system","Sos un experto en huerta organica argentina."),
            messages=messages)
        return jsonify({"reply": r.content[0].text})
    except Exception as e: return jsonify({"error": str(e)}), 500
@app.route("/analizar-planta", methods=["POST"])
def analizar_planta():
    try:
        data = request.json
        img = data.get("image")
        mt = data.get("media_type","image/jpeg")
        if not img: return jsonify({"error": "No image"}), 400
        r = client.messages.create(model="claude-opus-4-5", max_tokens=1200,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":mt,"data":img}},
                {"type":"text","text":"Analiza esta planta y responde SOLO JSON valido sin markdown: {\"planta\":\"nombre\",\"confianza\":\"alta/media/baja\",\"estado_general\":\"desc\",\"carencias\":[{\"nutriente\":\"X\",\"sintoma\":\"X\",\"solucion\":\"X\"}],\"excesos\":[{\"nutriente\":\"X\",\"sintoma\":\"X\",\"solucion\":\"X\"}],\"recomendacion_principal\":\"X\",\"abono_sugerido\":\"X\"}"}
            ]}])
        return jsonify(json.loads(r.content[0].text.strip()))
    except Exception as e: return jsonify({"error": str(e)}), 500
@app.route("/health")
def health(): return jsonify({"status":"ok","app":"BioHuerta v4.0"})
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
