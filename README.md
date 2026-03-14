# BioHuerta Intelligent v3.0
Asistente de huerta organica con IA (Claude) - Python Flask + HTML

## Deploy en Render
1. Conectar este repo en render.com
2. Start command: gunicorn app:app
3. Variable de entorno: ANTHROPIC_API_KEY

## Local (Termux)
pip install -r requirements.txt
export ANTHROPIC_API_KEY="tu_key"
python app.py
