
import streamlit as st
import json
import os
import requests
import time
from datetime import datetime
from duckduckgo_search import DDGS

# Cargar memoria
if "rafael" not in st.session_state:
    with open("memoria_rafael.json", "r", encoding="utf-8") as f:
        st.session_state.rafael = json.load(f)
if "conversacion" not in st.session_state:
    st.session_state.conversacion = []

HF_TOKEN = os.environ.get("HF_TOKEN")
HF_MODEL = "google/flan-t5-large"
HF_API = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def generar_respuesta(prompt, reintentos=3):
    data = {"inputs": prompt, "max_new_tokens": 200}
    for intento in range(reintentos):
        try:
            r = requests.post(HF_API, headers=HEADERS, json=data, timeout=30)
            r.raise_for_status()
            output = r.json()
            if isinstance(output, list) and output:
                respuesta = output[0].get("generated_text", "").strip()
                return respuesta if respuesta else "(Respuesta vacía. Intentá otra vez.)"
            return f"(Error inesperado en la respuesta del modelo: {output})"
        except requests.exceptions.HTTPError as e:
            if r.status_code in [502, 503, 504] and intento < reintentos - 1:
                time.sleep(2 + intento)
                continue
            return f"(Error de Hugging Face: {str(e)})"
        except Exception as e:
            return f"(Error interno: {str(e)})"
    return "(El modelo no respondió tras varios intentos.)"

def buscar_en_internet(texto):
    if texto.lower().startswith("busca en internet") or texto.lower().startswith("googlea"):
        consulta = texto.split(" ", 2)[-1]
        with DDGS() as ddgs:
            resultados = ddgs.text(consulta, max_results=1)
            for r in resultados:
                return f"Busqué y encontré esto: {r['title']} — {r['href']}"
    return None

def aprender(clave, valor, fuente="tú"):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    rafael = st.session_state.rafael
    rafael["aprendizajes"] = rafael.get("aprendizajes", {})
    historial = rafael["aprendizajes"].get(clave, {"versiones": [], "actual": None})
    if historial["actual"] != valor:
        if historial["actual"]:
            historial["versiones"].append({
                "valor": historial["actual"],
                "fecha": fecha,
                "fuente": "anterior"
            })
        historial["actual"] = valor
        historial["versiones"].append({
            "valor": valor,
            "fecha": fecha,
            "fuente": fuente
        })
    rafael["aprendizajes"][clave] = historial
    with open("memoria_rafael.json", "w", encoding="utf-8") as f:
        json.dump(rafael, f, ensure_ascii=False, indent=2)
    return f"¡Listo! Aprendí algo nuevo sobre {clave}."

def responder(texto):
    if texto.startswith("+"):
        try:
            clave, valor = texto[1:].strip().split(":", 1)
            return aprender(clave.strip(), valor.strip())
        except:
            return "¿Podés escribirlo como '+ tema: valor'?"
    internet = buscar_en_internet(texto)
    if internet:
        return internet
    if "cómo me llamo" in texto.lower():
        for k, v in st.session_state.rafael.get("aprendizajes", {}).items():
            if "llamas" in k:
                return f"¡Tú me dijiste que te llamas {v['actual']}! ¿Sigue siendo así?"
    return generar_respuesta(f"Pregunta: {texto}\nRespuesta:")

# Interfaz
st.title("R4F4EL - X (FLAN-T5-Large — Formato Pregunta/Respuesta)")
entrada = st.text_input("¿Qué le querés decir a Rafael?", key="entrada")

if entrada:
    respuesta = responder(entrada)
    st.session_state.conversacion.append((entrada, respuesta))
    st.text_area("Rafael responde:", value=respuesta, height=100)

st.markdown("## Conversación reciente")
for i, (t, r) in enumerate(reversed(st.session_state.conversacion[-5:])):
    st.markdown(f"**Tú:** {t}")
    st.markdown(f"**Rafael:** {r}")
