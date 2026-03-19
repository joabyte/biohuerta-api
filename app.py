from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic, json, os
app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY",""))

@app.route("/")
def index(): return send_from_directory(".", "index.html")

@app.route("/health")
def health(): return jsonify({"status":"ok","app":"BioHuerta v4.0"})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        if not messages: return jsonify({"error": "No messages"}), 400
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1000,
            system=data.get("system","Sos un experto en huerta organica argentina."),
            messages=messages)
        return jsonify({"reply": r.content[0].text})
    except anthropic.AuthenticationError:
        return jsonify({"error": "API key invalida"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analizar-planta", methods=["POST"])
def analizar_planta():
    try:
        data = request.json or {}
        img = data.get("image","")
        mt = data.get("media_type","image/jpeg")
        if not img: return jsonify({"error": "No se recibio imagen"}), 400
        PROMPT = (
            "Sos un botanico experto en horticultura. "
            "Analiza esta imagen con mucho detalle.\n\n"
            "PASO 1 - IDENTIFICACION:\n"
            "- Observa forma de hojas, nervaduras, textura, brillo\n"
            "- Observa tallo, color, grosor\n"
            "- Observa flores, frutos o raices visibles\n"
            "- Si hay texto visible en la imagen usalo como pista\n"
            "- Si no estas seguro al 90%, pon confianza baja\n\n"
            "PASO 2 - ESTADO SANITARIO:\n"
            "- Revisa color de hojas y patrones de amarillamiento\n"
            "- Detecta signos de plagas: agujeros, telas, manchas\n\n"
            "PASO 3 - DIAGNOSTICO:\n"
            "- Nitrogeno: amarillamiento uniforme en hojas viejas\n"
            "- Hierro: amarillamiento intervenal en hojas jovenes\n"
            "- Magnesio: amarillamiento intervenal en hojas viejas\n"
            "- Calcio: puntas marrones en hojas jovenes\n"
            "- Potasio: bordes quemados en hojas viejas\n\n"
            "Responde UNICAMENTE con JSON valido sin markdown:\n"
            '{"planta":"nombre comun especifico",'
            '"confianza":"alta/media/baja",'
            '"razon_confianza":"explicacion",'
            '"estado_general":"estado en 1-2 oraciones",'
            '"carencias":[{"nutriente":"X","sintoma":"X","solucion":"X"}],'
            '"excesos":[{"nutriente":"X","sintoma":"X","solucion":"X"}],'
            '"plagas_detectadas":"ninguna o descripcion",'
            '"recomendacion_principal":"accion urgente",'
            '"abono_sugerido":"producto organico"}')
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1500,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":mt,"data":img}},
                {"type":"text","text":PROMPT}
            ]}])
        texto = r.content[0].text.strip()
        if "```" in texto:
            for p in texto.split("```"):
                p2=p.strip()
                if p2.startswith("json"): p2=p2[4:].strip()
                if p2.startswith("{"): texto=p2; break
        return jsonify(json.loads(texto))
    except anthropic.AuthenticationError:
        return jsonify({"error": "API key invalida. Configurar en Render > Environment"}), 401
    except json.JSONDecodeError as e:
        return jsonify({"error": "JSON invalido: "+str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
