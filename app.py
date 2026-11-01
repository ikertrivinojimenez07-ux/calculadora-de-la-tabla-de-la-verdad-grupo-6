
import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad", layout="centered")

st.title("🧮 Calculadora de Tabla de la Verdad")
st.markdown("Construye tu expresión haciendo clic. El resultado se mostrará **exclusivamente en 0 y 1**.")

# --- Estado de la sesión ---
if "expr" not in st.session_state:
    st.session_state.expr = ""

# --- UI: Constructor de Expresión ---
st.subheader("📋 Constructor de Expresión")

cols = st.columns(6)
# Variables configuradas estrictamente en minúsculas
variables = ["p", "q", "r", "s", "t", "u"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

st.markdown("---")

st.subheader("➕ Operadores")

cols = st.columns(5)
# Lista estricta de operadores en sus símbolos formales matemáticos
operadores = ["∧", "∨", "→", "↔", "¬", "(", ")", "[", "]", "{", "}"]
for i, op in enumerate(operadores):
    with cols[i % 5]:
        if st.button(f"{op}", key=f"btn_{i}", use_container_width=True):
            st.session_state.expr += f" {op} "

col_limpiar, col_preview, col_gen = st.columns(3)

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    st.code(st.session_state.expr.strip() or "(vacío)", language="text")

# --- Lógica Central ---
def normalizar_expresion(expr: str) -> str:
    # Mantenemos las minúsculas originales para las variables
    e = expr.strip()
    
    # 1. Homologar todos los signos de agrupación (corchetes y llaves) a paréntesis normales de Python
    e = e.replace('[', '(').replace(']', ')')
    e = e.replace('{', '(').replace('}', ')')
    
    # 2. Traducir símbolos lógicos formales a operadores lógicos de Python
    e = re.sub(r'∧', ' and ', e)
    e = re.sub(r'∨', ' or ', e)
    e = re.sub(r'¬', ' not ', e)
    
    # 3. Procesar condicionales (→) y bicondicionales (↔) usando patrones en minúsculas
    for _ in range(5):
        e = re.sub(r'([a-z0-9\)]+)\s*(→)\s*([a-z0-9\(\~]+)', r'(not \1 or \3)', e)
        e = re.sub(r'([a-z0-9\)]+)\s*(↔)\s*([a-z0-9\(\~]+)', r'(\1 == \3)', e)
    
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    # Extrae únicamente las variables válidas de la 'p' a la 'u' en minúsculas
    return sorted(list(set(re.findall(r'\b[p-u]\b', expr))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
        
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_raw)
    
    if not variables:
        return [], []
        
    tabla = []
    
    # Generar la matriz binaria iterando sobre las permutaciones
    for valores in product([1, 0], repeat=len(variables)):
        entorno = {v: bool(val) for val, v in zip(valores, variables)}
        try:
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            fila = list(valores) + [int(bool(resultado))]
            tabla.append(fila)
        except Exception:
            return [], []
            
    return variables, tabla

# --- Ejecución ---
with col_gen:
    btn_generar = st.button("🚀 Generar Tabla", type="primary", use_container_width=True)

if btn_generar:
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars, tabla = generar_tabla(st.session_state.expr)
        
        if not vars:
            st.error("❌ Expresión inválida o sin variables detectadas.")
        else:
            cols_df = vars + ["Resultado"]
            df = pd.DataFrame(tabla, columns=cols_df)
            
            st.success(f"📊 Tabla generada para {len(vars)} variable(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
