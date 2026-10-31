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

col_limpiar, col_preview, col_gen = st.columns(3)

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    expr_actual = st.session_state.expr.strip()
    st.code(expr_actual if expr_actual else "(vacío)", language="text")

# --- Lógica Central Optimizada ---
def segmentar_operandos(tokens: list, idx_op: int) -> tuple:
    """Busca los límites del operando izquierdo y derecho alrededor de un operador binario."""
    # Encontrar límite izquierdo
    izq = idx_op - 1
    if tokens[izq] == ')':
        balance = 1
        izq -= 1
        while izq >= 0 and balance > 0:
            if tokens[izq] == ')': balance += 1
            elif tokens[izq] == '(': balance -= 1
            izq -= 1
        izq += 1
    elif tokens[izq] == 'not':
        # Incluir el 'not' y su variable correspondiente
        if izq - 1 >= 0 and tokens[izq - 1] == 'not':
            izq -= 1
    
    # Encontrar límite derecho
    der = idx_op + 1
    if tokens[der] == 'not':
        der += 1
    if tokens[der] == '(':
        balance = 1
        der += 1
        while der < len(tokens) and balance > 0:
            if tokens[der] == '(': balance += 1
            elif tokens[der] == ')': balance -= 1
            der += 1
    else:
        der += 1
        
    return izq, der

def normalizar_expresion(expr: str) -> str:
    # 1. Reemplazo de delimitadores a formato único
    e = expr.strip()
    e = e.replace('[', '(').replace(']', ')')
    e = e.replace('{', '(').replace('}', ')')
    
    # 2. Traducción de operadores simples
    e = re.sub(r'¬', ' not ', e)
    e = re.sub(r'∧', ' and ', e)
    e = re.sub(r'∨', ' or ', e)
    e = re.sub(r'⊕', ' != ', e)
    
    # 3. Procesar condicionales complejos (→ y ↔) convirtiendo tokens
    # Separar todo manteniendo los paréntesis intactos
    tokens = re.findall(r'\(|\)|not|and|or|!=|→|↔|[p-u]', e)
    
    # Procesar primero Equivalencias (↔) e Implicaciones (→) recurrentemente
    while '→' in tokens or '↔' in tokens:
        # Buscamos el primer operador condicional disponible
        idx_op = next((i for i, t in enumerate(tokens) if t in ('→', '↔')), None)
        if idx_op is None:
            break
            
        op = tokens[idx_op]
        izq, der = segmentar_operandos(tokens, idx_op)
        
        expr_izq = " ".join(tokens[izq:idx_op])
        expr_der = " ".join(tokens[idx_op+1:der])
        
        # Aplicamos identidades lógicas puras compatibles con Python eval()
        if op == '→':
            nueva_sub_expr = f"(not ({expr_izq}) or ({expr_der}))"
        else: # op == '↔'
            nueva_sub_expr = f"(({expr_izq}) == ({expr_der}))"
            
        # Reemplazar el segmento antiguo procesado por los nuevos tokens estructurados
        nuevos_tokens_sub = re.findall(r'\(|\)|not|and|or|!=|→|↔|[p-u]|==', nueva_sub_expr)
        tokens = tokens[:izq] + nuevos_tokens_sub + tokens[der:]
        
    return " ".join(tokens)

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
    
    # Orden de las permutaciones (Verdadero arriba, Falso abajo en binario)
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
