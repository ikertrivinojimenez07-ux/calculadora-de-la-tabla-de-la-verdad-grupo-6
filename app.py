import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered")

# Título oficial solicitado con el identificador del grupo
st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")
st.markdown("Construye tu expresión usando los botones o selecciona un ejemplo rápido. El resultado se calcula automáticamente en **0 y 1**.")

# --- Estado de la sesión (Session State) ---
if "expr" not in st.session_state:
    st.session_state.expr = ""

# --- UI: Constructor de Expresión ---
st.subheader("🛠️ Constructor de Expresión")

# Variables soportadas por el sistema: p, q, r, s, t, u
cols = st.columns(6)
variables = ["p", "q", "r", "s", "t", "u"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

st.markdown("---")
st.subheader("➕ Operadores")

# Operadores asignados en cuadrícula
cols = st.columns(6)
operadores = ["∧", "∨", "¬", "⊕", "→", "↔", "(", ")"]

for i, op in enumerate(operadores):
    with cols[i % 6]:
        if st.button(op, key=f"btn_{op}", use_container_width=True):
            st.session_state.expr += f" {op} "

# Botones de control de limpieza distribuidos uniformemente
col_limpiar, col_borrar = st.columns(2)

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

# Mostrar expresión actualmente acumulada
st.markdown("### Expresión actual:")
expr_limpia = st.session_state.expr.strip()
if not expr_limpia:
    st.code("(vacío)", language="text")
else:
    st.code(expr_limpia, language="text")

# --- Sección de Ejemplos Rápidos solicitados en tus imágenes ---
st.markdown("### Ejemplos rápidos:")
ejemplos = [
    "p ∧ q", "p ∨ q", "p ⊕ q",
    "p → q", "p ↔ q", "¬ p",
    "(p → q) ↔ (¬q → ¬p)", "p ∨ ¬p", "p ∧ ¬p"
]
cols_ej = st.columns(3)
for i, ej in enumerate(ejemplos):
    with cols_ej[i % 3]:
        if st.button(ej, key=f"ej_{i}", use_container_width=True):
            st.session_state.expr = f" {ej} "

st.markdown("---")

# --- Motor de Evaluación Lógica (Parser Jerárquico Avanzado) ---
def normalizar_cadena(expr: str) -> str:
    # Reemplaza cualquier variante de caracteres invisibles o tipografías alternativas
    # que provengan tanto de clics de botones como de pegado de texto.
    cadena = expr.strip()
    cadena = cadena.replace("~", "¬").replace("-", "¬")
    cadena = cadena.replace("+", "⊕")
    cadena = cadena.replace("^", "∧").replace("v", "∨")
    return cadena

def tokenize(expr: str) -> list:
    cadena_limpia = normalizar_cadena(expr)
    # Extrae los tokens lógicos exactos ignorando cualquier tipo de espaciado irregular
    return re.findall(r'[pqrstu]|∧|∨|¬|⊕|→|↔|\(|\)', cadena_limpia)

def evaluar_con_entorno(tokens: list, env: dict) -> bool:
    # 1. Resolver los bloques dentro de paréntesis de adentro hacia afuera recursivamente
    while "(" in tokens:
        start = max([i for i, t in enumerate(tokens) if t == "("])
        end = tokens.index(")", start)
        sub_resultado = evaluar_con_entorno(tokens[start + 1:end], env)
        tokens[start:end + 1] = [sub_resultado]
    
    def obtener_valor(t):
        if isinstance(t, bool):
            return t
        return env.get(t, False)

    # 2. Prioridad 1: Negaciones (¬) de derecha a izquierda
    while "¬" in tokens:
        idx = max([i for i, t in enumerate(tokens) if t == "¬"])
        if idx + 1 < len(tokens):
            tokens[idx:idx + 2] = [not obtener_valor(tokens[idx + 1])]
        else:
            raise ValueError()

    # 3. Prioridad 2: Conjunción (∧), Disyunción (∨) y XOR (⊕) de izquierda a derecha
    i = 0
    while i < len(tokens):
        if tokens[i] in ["∧", "∨", "⊕"]:
            op = tokens[i]
            izq = obtener_valor(tokens[i - 1])
            der = obtener_valor(tokens[i + 1])
            if op == "∧": res = izq and der
            elif op == "∨": res = izq or der
            elif op == "⊕": res = izq != der
            tokens[i - 1:i + 2] = [res]
            i -= 1
        i += 1

    # 4. Prioridad 3: Condicional (→) de izquierda a derecha
    i = 0
    while i < len(tokens):
        if tokens[i] == "→":
            izq = obtener_valor(tokens[i - 1])
            der = obtener_valor(tokens[i + 1])
            res = (not izq) or der  # Equivalencia lógica del condicional
            tokens[i - 1:i + 2] = [res]
            i -= 1
        i += 1

    # 5. Prioridad 4: Bicondicional (↔) de izquierda a derecha
    i = 0
    while i < len(tokens):
        if tokens[i] == "↔":
            izq = obtener_valor(tokens[i - 1])
            der = obtener_valor(tokens[i + 1])
            res = izq == der
            tokens[i - 1:i + 2] = [res]
            i -= 1
        i += 1

    return obtener_valor(tokens)

def extraer_variables(expr: str) -> list:
    cadena_limpia = normalizar_cadena(expr)
    return sorted(list(set(re.findall(r'[pqrstu]', cadena_limpia.lower()))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
        
    variables = extraer_variables(expr_raw)
    if not variables:
        return [], []
        
    try:
        tokens_originales = tokenize(expr_raw)
        if not tokens_originales:
            return [], []
    except Exception:
        return [], []
        
    tabla = []
    # Genera el árbol combinatorio exacto en formato binario clásico descendente (1 antes que 0)
    for valores in product((1, 0), repeat=len(variables)):
        entorno = {v: bool(val) for val, v in zip(valores, variables)}
        try:
            resultado = evaluar_con_entorno(list(tokens_originales), entorno)
            fila = list(valores) + [1 if resultado else 0]
            tabla.append(fila)
        except Exception:
            return [], []
            
    return variables, tabla

# --- Ejecución y renderizado del DataFrame ---
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
            # Forzar la visualización estricta en formato de enteros 0 y 1 sin decimales
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Generación automática del archivo descargable CSV
            csv = df.to_csv(index=False).encode("utf-8")
            