from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic, json, os, threading, urllib.request, time
app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY",""))

def keep_alive():
    time.sleep(60)
    url=os.environ.get("RENDER_EXTERNAL_URL","")
    if not url: return
    while True:
        try: urllib.request.urlopen(url+"/health",timeout=10)
        except: pass
        time.sleep(600)

threading.Thread(target=keep_alive,daemon=True).start()

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
        if not img: return jsonify({"error":"No imagen"}),400
        P=("Sos un botanico experto. Analiza esta imagen con detalle.\n"
           "IDENTIFICACION: forma de hojas, nervaduras, textura, tallo, flores, frutos.\n"
           "Si ves texto en la imagen usalo. Si no estas seguro 90%, confianza baja.\n"
           "ESTADO: color hojas, amarillamiento, plagas.\n"
           "DIAGNOSTICO: Nitrogeno=amarillamiento uniforme hojas viejas, "
           "Hierro=amarillamiento intervenal hojas jovenes, "
           "Magnesio=amarillamiento intervenal hojas viejas, "
           "Calcio=puntas marrones hojas jovenes, "
           "Potasio=bordes quemados hojas viejas.\n"
           "Responde SOLO JSON sin markdown: "
           '{"planta":"nombre","confianza":"alta/media/baja","razon_confianza":"x",'
           '"estado_general":"x","carencias":[{"nutriente":"x","sintoma":"x","solucion":"x"}],'
           '"excesos":[{"nutriente":"x","sintoma":"x","solucion":"x"}],'
           '"plagas_detectadas":"ninguna o desc","recomendacion_principal":"x","abono_sugerido":"x"}')
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
    except anthropic.AuthenticationError: return jsonify({"error":"API key invalida"}),401
    except json.JSONDecodeError as e: return jsonify({"error":"JSON invalido: "+str(e)}),500
    except Exception as e: return jsonify({"error":str(e)}),500
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
