import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered")

# Título con el identificador del grupo
st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")
st.markdown("Construye tu expresión haciendo clic. El resultado se muestra en **0 y 1**.")

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

# Operadores alineados con la interfaz
cols = st.columns(6)
operadores = ["∧", "∨", "¬", "⊕", "→", "↔", "(", ")"]

for i, op in enumerate(operadores):
    with cols[i % 6]:
        if st.button(op, key=f"btn_{op}", use_container_width=True):
            st.session_state.expr += f" {op} "

# Botones de control de limpieza y borrado
col_limpiar, col_borrar, _ = st.columns([1, 1, 2])

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

# --- Lógica Central Optimizada ---
def normalizar_expresion(expr: str) -> str:
    # Limpiamos espacios iniciales y finales
    e = expr.strip()
    
    # 1. Reemplazar los operadores lógicos básicos y directos
    e = e.replace("∧", " and ")
    e = e.replace("∨", " or ")
    e = e.replace("¬", " not ")
    e = e.replace("⊕", " != ")  # XOR
    
    # 2. Reemplazar Bicondicional (↔) por equivalencia de igualdad (==)
    e = e.replace("↔", " == ")
    
    # 3. Lógica robusta para el Condicional (→) sin romper paréntesis complejos:
    # En lógica: (A → B) es exactamente equivalente a (not A or B)
    # Buscamos de derecha a izquierda para respetar la asociatividad correcta
    while "→" in e:
        # Buscamos el último condicional para resolver de adentro hacia afuera o derecha a izquierda
        idx = e.rfind("→")
        izquierda = e[:idx].strip()
        derecha = e[idx+1:].strip()
        
        # Envolvemos de manera segura la equivalencia condicional
        e = f"(not ({izquierda}) or ({derecha}))"
        
    # Limpieza de espacios múltiples remanentes
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    # Extrae únicamente las variables declaradas p, q, r, s, t, u
    return sorted(list(set(re.findall(r'\b[pqrstu]\b', expr))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
        
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_raw)
    
    if not variables:
        return [], []
        
    tabla = []
    
    # Generar combinaciones binarias de verdad usando 1 y 0
    for valores in product([1, 0], repeat=len(variables)):
        # Pasamos las variables como booleanos nativos a Python para evaluar de forma segura
        entorno = {v: bool(val) for val, v in zip(valores, variables)}
        try:
            # Evaluación limpia dentro de un entorno controlado
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            # Volvemos a convertir el booleano a formato numérico 1 o 0
            fila = list(valores) + [1 if resultado else 0]
            tabla.append(fila)
        except Exception as err:
            # En caso de error de sintaxis en el eval, retorna vacío para lanzar la alerta
            return [], []
            
    return variables, tabla

# --- Ejecución ---
if st.button("📊 Generar Tabla", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_list, tabla_data = generar_tabla(st.session_state.expr)
        
        if not vars_list or not tabla_data:
            st.error("❌ Expresión inválida o estructura mal construida. Revisa los paréntesis y operadores.")
        else:
            cols_df = vars_list + ["Resultado"]
            df = pd.DataFrame(tabla_data, columns=cols_df)
            
            st.success(f"✅ Tabla generada con éxito para {len(vars_list)} variable(s).")
            # Presentar tabla en el formato solicitado (Estrictamente en 0 y 1)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Descarga del archivo final
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
