import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered")

# --- Título Actualizado ---
st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")
st.markdown("Construye tu expresión haciendo clic. El resultado se mostrará **exclusivamente en 0 y 1**.")

# --- Estado de la Sesión ---
if "expr" not in st.session_state:
    st.session_state.expr = ""

# --- 01. Constructor de Expresión ---
st.subheader("⚙️ Constructor de Expresión")

# Variables solicitadas: de p a u en minúsculas
variables = ["p", "q", "r", "s", "t", "u"]
cols_vars = st.columns(6)

for i, v in enumerate(variables):
    with cols_vars[i]:
        if st.button(v, key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

st.markdown("---")

st.subheader("➕ Operadores")
# Diccionario para mostrar símbolos en los botones
operadores_dict = {
    "¬ NOT": "¬",
    "∧ AND": "∧",
    "∨ OR": "∨",
    "⊕ XOR": "⊕",
    "→ IMPL": "→",
    "↔ EQUIV": "↔",
    "( ": "(",
    " )": ")"
}

operadores = list(operadores_dict.keys())
cols_ops = st.columns(4)

for i, op_label in enumerate(operadores):
    with cols_ops[i % 4]:
        if st.button(op_label, key=f"btn_{op_label.strip()}", use_container_width=True):
            simbolo = operadores_dict[op_label]
            if simbolo == "¬":
                st.session_state.expr += f" {simbolo} "
            else:
                st.session_state.expr += f" {simbolo} "

col_limpiar, col_preview, col_gen = st.columns()

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    expr_actual = st.session_state.expr.strip()
    st.code(expr_actual if expr_actual else "(vacío)", language="text")

# --- Lógica Central ---
def normalizar_expresion(expr: str) -> str:
    # Convertimos los símbolos visuales a operadores lógicos de Python
    e = expr.strip()
    e = re.sub(r'¬', ' not ', e)
    e = re.sub(r'∧', ' and ', e)
    e = re.sub(r'∨', ' or ', e)
    e = re.sub(r'⊕', ' != ', e) # XOR lógico en booleanos es equivalente a !=
    
    # Implicación (p → q) es equivalente a (not p or q)
    e = re.sub(r'([a-z0-9)]+)\s*→\s*([a-z0-9(]+)', r'(not \1 or \2)', e)
    # Equivalencia (p ↔ q) es equivalente a (p == q)
    e = re.sub(r'([a-z0-9)]+)\s*↔\s*([a-z0-9(]+)', r'(\1 == \2)', e)
    
    # Limpiar espacios dobles
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    # Busca letras minúsculas individuales de la p a la u
    return sorted(list(set(re.findall(r'\b[p-u]\b', expr))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
        
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_raw)
    
    if not variables:
        return [], []
        
    tabla = []
    
    # Generamos combinaciones directamente en True/False (evaluadas como 1 y 0 después)
    for valores in product([True, False], repeat=len(variables)):
        entorno = dict(zip(variables, valores))
        try:
            # Evaluamos de forma segura con eval sin funciones globales peligrosas
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            
            # Formateamos la fila convirtiendo True -> 1 y False -> 0
            fila = [1 if v else 0 for v in valores] + [1 if resultado else 0]
            tabla.append(fila)
        except Exception:
            return [], []
            
    return variables, tabla

# --- Ejecución ---
with col_gen:
    btn_generar = st.button("📊 Generar", type="primary", use_container_width=True)

if btn_generar:
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_det, tabla_det = generar_tabla(st.session_state.expr)
        
        if not vars_det:
            st.error("❌ Expresión inválida o sin variables detectadas.")
        else:
            cols_df = vars_det + ["Resultado"]
            df = pd.DataFrame(tabla_det, columns=cols_df)
            
            st.success(f"🎰 Tabla generada para {len(vars_det)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
