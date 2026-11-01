import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered")

# Modificado para incluir el Grupo 6 en el título
st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")
st.markdown("Construye tu expresión haciendo clic. El resultado se mostrará **exclusivamente en 0 y 1**.")

# --- Estado de la sesión ---
if "expr" not in st.session_state:
    st.session_state.expr = ""

# --- UI: Constructor de Expresión ---
st.subheader("🛠️ Constructor de Expresión")

# Variables: p, q, r, s, t, u
cols = st.columns(6)
variables = ["p", "q", "r", "s", "t", "u"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

st.markdown("---")
st.subheader("➕ Operadores")

# Operadores y acciones de limpieza
cols = st.columns(6)
operadores = ["∧", "∨", "¬", "⊕", "→", "↔", "(", ")"]

# Mapeo visual a la interfaz de columnas
for i, op in enumerate(operadores):
    with cols[i % 6]:
        if st.button(op, key=f"btn_{op}", use_container_width=True):
            st.session_state.expr += f" {op} "

# Botones de control de limpieza y borrado
col_limpiar, col_borrar, col_gen = st.columns([2, 2, 2])

with col_limpiar:
    if st.button("🗑️ Limpiar Todo", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_borrar:
    if st.button("⌫ Borrar Último", type="secondary", use_container_width=True):
        tokens = st.session_state.expr.strip().split()
        if tokens:
            tokens.pop()
            st.session_state.expr = " " + " ".join(tokens) + " "
        else:
            st.session_state.expr = ""

# Mostrar expresión actual
st.markdown("### Expresión actual:")
expr_limpia = st.session_state.expr.strip()
if not expr_limpia:
    st.code("(vacío)", language="text")
else:
    st.code(expr_limpia, language="text")

# Ejemplos rápidos
st.markdown("### Ejemplos rápidos:")
ejemplos = ["p ∧ q", "p ∨ q", "p ⊕ q", "p → q", "p ↔ q", "¬ p"]
cols_ej = st.columns(3)
for i, ej in enumerate(ejemplos):
    with cols_ej[i % 3]:
        if st.button(ej, key=f"ej_{i}", use_container_width=True):
            st.session_state.expr = f" {ej} "

st.markdown("---")

# --- Lógica Central ---
def normalizar_expresion(expr: str) -> str:
    # Convertir operadores visuales a operadores lógicos de Python
    e = expr.strip()
    e = e.replace("∧", " and ")
    e = e.replace("∨", " or ")
    e = e.replace("¬", " not ")
    e = e.replace("⊕", " != ")  # XOR es equivalente a la desigualdad en booleanos
    
    # Condicional (p → q) convertido a (~p ∨ q) -> (not p or q)
    # Se busca patrones como: expresión -> expresión
    # Para simplificar la evaluación directa segura con expresiones binarias simples:
    e = re.sub(r'(\w+|\([^)]+\))\s*→\s*(\w+|\([^)]+\))', r'(not \1 or \2)', e)
    
    # Bicondicional (p ↔ q) convertido a (p == q)
    e = re.sub(r'(\w+|\([^)]+\))\s*↔\s*(\w+|\([^)]+\))', r'(\1 == \2)', e)
    
    # Limpieza de espacios dobles
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    # Extraer las letras individuales de variables (p, q, r, s, t, u)
    return sorted(list(set(re.findall(r'\b[pqrstu]\b', expr))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
        
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_raw)
    
    if not variables:
        return [], []
        
    tabla = []
    
    # Generar combinaciones directamente en 0 y 1
    for valores in product([1, 0], repeat=len(variables)):
        # Diccionario de entorno evaluando las variables reales de Python como booleanos
        entorno = {v: bool(val) for val, v in zip(valores, variables)}
        try:
            # Evaluar la expresión normalizada de forma segura
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            # Guardar el registro convirtiendo los booleanos de nuevo a 1 y 0
            fila = list(valores) + [1 if resultado else 0]
            tabla.append(fila)
        except Exception:
            return [], []
            
    return variables, tabla

# --- Ejecución ---
if st.button("📊 Generar Tabla", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_list, tabla_data = generar_tabla(st.session_state.expr)
        
        if not vars_list:
            st.error("❌ Expresión inválida o sin variables detectadas.")
        else:
            cols_df = vars_list + ["Resultado"]
            df = pd.DataFrame(tabla_data, columns=cols_df)
            
            st.success(f"✅ Tabla generada para {len(vars_list)} variable(s).")
            # Mostrar la tabla formateando los valores estrictamente como enteros (0 y 1)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Botón para descargar el archivo CSV resultante
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")

