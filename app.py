import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered")

# --- Título ---
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

# Lista con solo los símbolos solicitados (incluyendo corchetes y llaves)
operadores = ["¬", "∧", "∨", "⊕", "→", "↔", "(", ")", "[", "]", "{", "}"]
cols_ops = st.columns(4)

for i, simbolo in enumerate(operadores):
    with cols_ops[i % 4]:
        if st.button(simbolo, key=f"btn_op_{i}", use_container_width=True):
            st.session_state.expr += f" {simbolo} "

# ERROR SOLUCIONADO: Se definió st.columns(3) con el número correcto de columnas
col_limpiar, col_preview, col_gen = st.columns(3)

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    expr_actual = st.session_state.expr.strip()
    st.code(expr_actual if expr_actual else "(vacío)", language="text")

# --- Lógica Central ---
def normalizar_expresion(expr: str) -> str:
    e = expr.strip()
    
    # Homologamos llaves y corchetes a paréntesis normales para que Python los entienda
    e = e.replace('[', '(').replace(']', ')')
    e = e.replace('{', '(').replace('}', ')')
    
    # Convertimos los símbolos visuales a operadores lógicos de Python
    e = re.sub(r'¬', ' not ', e)
    e = re.sub(r'∧', ' and ', e)
    e = re.sub(r'∨', ' or ', e)
    e = re.sub(r'⊕', ' != ', e)
    
    # Implicación (p → q) es equivalente a (not p or q)
    e = re.sub(r'([a-z0-9)]+)\s*→\s*([a-z0-9(]+)', r'(not \1 or \2)', e)
    # Equivalencia (p ↔ q) es equivalente a (p == q)
    e = re.sub(r'([a-z0-9)]+)\s*↔\s*([a-z0-9(]+)', r'(\1 == \2)', e)
    
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    return sorted(list(set(re.findall(r'\b[p-u]\b', expr))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
        
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_raw)
    
    if not variables:
        return [], []
        
    tabla = []
    
    for valores in product([True, False], repeat=len(variables)):
        entorno = dict(zip(variables, valores))
        try:
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
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
