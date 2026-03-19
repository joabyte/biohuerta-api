from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic, json, os
app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY",""))
@app.route("/")
def index(): return send_from_directory(".", "index.html")
@app.route("/health")
def health(): return jsonify({"status":"ok"})
@app.route("/chat", methods=["POST"])
def chat():
    try:
        d=request.json or {}
        msgs=d.get("messages",[])
        if not msgs: return jsonify({"error":"No messages"}),400
        r=client.messages.create(model="claude-opus-4-5",max_tokens=1000,
            system=d.get("system","Sos un experto en huerta organica argentina."),
            messages=msgs)
        return jsonify({"reply":r.content[0].text})
    except anthropic.AuthenticationError: return jsonify({"error":"API key invalida"}),401
    except Exception as e: return jsonify({"error":str(e)}),500
@app.route("/analizar-planta", methods=["POST"])
def analizar_planta():
    try:
        d=request.json or {}
        img=d.get("image","")
        mt=d.get("media_type","image/jpeg")
        if not img: return jsonify({"error":"No se recibio imagen"}),400
        P=("Sos un botanico experto en horticultura. "
           "Analiza esta imagen con detalle.\n\n"
           "PASO 1 IDENTIFICACION:\n"
           "Observa forma de hojas, nervaduras, textura, tallo, flores, frutos.\n"
           "Si hay texto visible en la imagen usalo como pista.\n"
           "Si no estas seguro al 90%, pon confianza baja.\n\n"
           "PASO 2 ESTADO:\n"
           "Revisa color de hojas y patrones de amarillamiento.\n"
           "Detecta signos de plagas: agujeros, telas, manchas.\n\n"
           "PASO 3 DIAGNOSTICO:\n"
           "Nitrogeno: amarillamiento uniforme hojas viejas.\n"
           "Hierro: amarillamiento intervenal hojas jovenes.\n"
           "Magnesio: amarillamiento intervenal hojas viejas.\n"
           "Calcio: puntas marrones hojas jovenes.\n"
           "Potasio: bordes quemados hojas viejas.\n\n"
           "Responde SOLO con JSON sin markdown:\n"
           '{"planta":"nombre comun","confianza":"alta/media/baja",'
           '"razon_confianza":"explicacion","estado_general":"estado",'
           '"carencias":[{"nutriente":"X","sintoma":"X","solucion":"X"}],'
           '"excesos":[{"nutriente":"X","sintoma":"X","solucion":"X"}],'
           '"plagas_detectadas":"ninguna o descripcion",'
           '"recomendacion_principal":"accion urgente",'
           '"abono_sugerido":"producto organico"}')
        r=client.messages.create(model="claude-opus-4-5",max_tokens=1500,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":mt,"data":img}},
                {"type":"text","text":P}]}])
        t=r.content[0].text.strip()
        if "```" in t:
            for p in t.split("```"):
                p2=p.strip()
                if p2.startswith("json"): p2=p2[4:].strip()
                if p2.startswith("{"): t=p2; break
        return jsonify(json.loads(t))
    except anthropic.AuthenticationError: return jsonify({"error":"API key invalida. Configurar en Render > Environment"}),401
    except json.JSONDecodeError as e: return jsonify({"error":"JSON invalido: "+str(e)}),500
    except Exception as e: return jsonify({"error":str(e)}),500
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
