
import streamlit as st
import json
import os
import requests
from datetime import datetime
from duckduckgo_search import DDGS

# Cargar memoria
if "rafael" not in st.session_state:
    with open("memoria_rafael.json", "r", encoding="utf-8") as f:
        st.session_state.rafael = json.load(f)
if "conversacion" not in st.session_state:
    st.session_state.conversacion = []

# Configurar Hugging Face Falcon 7B Instruct
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_MODEL = "tiiuae/falcon-7b-instruct"
HF_API = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def generar_respuesta(prompt):
    data = {"inputs": prompt, "max_new_tokens": 100}
    try:
        r = requests.post(HF_API, headers=HEADERS, json=data, timeout=20)
        r.raise_for_status()
        output = r.json()
        if isinstance(output, list):
            return output[0]["generated_text"].split("Respuesta:")[-1].strip()
        return str(output)
    except:
        return "No pude pensar eso bien aún... ¿me lo contás de nuevo?"

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
st.title("R4F4EL - X (con Falcon 7B Instruct)")
entrada = st.text_input("¿Qué le querés decir a Rafael?", key="entrada")

if entrada:
    respuesta = responder(entrada)
    st.session_state.conversacion.append((entrada, respuesta))
    st.text_area("Rafael responde:", value=respuesta, height=100)

st.markdown("## Conversación reciente")
for i, (t, r) in enumerate(reversed(st.session_state.conversacion[-5:])):
    st.markdown(f"**Tú:** {t}")
    st.markdown(f"**Rafael:** {r}")
