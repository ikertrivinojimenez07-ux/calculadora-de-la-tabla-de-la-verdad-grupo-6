import streamlit as st
from itertools import product
import pandas as pd
import re

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered")

# --- Título ---
st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")
st.markdown("Construye tu expresión haciendo clic de forma libre. Soporta cualquier nivel de anidamiento.")

# --- Estado de la Sesión ---
if "expr" not in st.session_state:
    st.session_state.expr = ""

# --- 01. Constructor de Expresión ---
st.subheader("⚙️ Constructor de Expresión")

VARIABLES_DISPONIBLES = ["p", "q", "r", "s", "t", "u"]
cols_vars = st.columns(6)

for i, v in enumerate(VARIABLES_DISPONIBLES):
    with cols_vars[i]:
        if st.button(v, key=f"btn_var_{v}", use_container_width=True):
            st.session_state.expr += f"{v}"

st.markdown("---")

st.subheader("➕ Operadores")

# Lista optimizada de símbolos puros solicitados
operadores = ["¬", "∧", "∨", "⊕", "→", "↔", "(", ")", "[", "]", "{", "}"]
cols_ops = st.columns(4)

for i, simbolo in enumerate(operadores):
    with cols_ops[i % 4]:
        if st.button(simbolo, key=f"btn_sym_{i}", use_container_width=True):
            st.session_state.expr += f"{simbolo}"

st.markdown("---")

col_limpiar, col_preview, col_gen = st.columns([1, 2, 1])

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""
        st.rerun()

with col_preview:
    expr_actual = st.session_state.expr.strip()
    st.code(expr_actual if expr_actual else "(vacío)", language="text")

# --- Lógica de Procesamiento Matemático Plano (Previene congelamiento) ---
def traducir_a_python(expr: str) -> str:
    # 1. Homologar delimitadores de agrupación
    e = expr.replace('[', '(').replace(']', ')').replace('{', '(').replace('}', ')')
    
    # 2. Tokenizar limpiamente de forma lineal
    tokens = re.findall(r'¬|∧|∨|⊕|→|↔|\(|\)|[p-u]', e)
    
    # 3. Procesar condicionales implicativos (→) de derecha a izquierda
    while '→' in tokens:
        idx = len(tokens) - 1 - tokens[::-1].index('→')
        izq_start = idx - 1
        if tokens[izq_start] == ')':
            balance = 1
            izq_start -= 1
            while izq_start >= 0 and balance > 0:
                if tokens[izq_start] == ')': balance += 1
                elif tokens[izq_start] == '(': balance -= 1
                izq_start -= 1
            izq_start += 1
        else:
            if izq_start - 1 >= 0 and tokens[izq_start - 1] == '¬':
                izq_start -= 1
                
        der_end = idx + 1
        if tokens[der_end] == '¬':
            der_end += 1
        if tokens[der_end] == '(':
            balance = 1
            der_end += 1
            while der_end < len(tokens) and balance > 0:
                if tokens[der_end] == '(': balance += 1
                elif tokens[der_end] == ')': balance -= 1
                der_end += 1
        else:
            der_end += 1
            
        expr_izq = tokens[izq_start:idx]
        expr_der = tokens[idx + 1:der_end]
        sub_combinada = ['(', '¬', '('] + expr_izq + [')', '∨', '('] + expr_der + [')', ')']
        tokens = tokens[:izq_start] + sub_combinada + tokens[der_end:]

    # 4. Procesar condicionales bicondicionales (↔)
    while '↔' in tokens:
        idx = tokens.index('↔')
        izq_start = idx - 1
        if tokens[izq_start] == ')':
            balance = 1
            izq_start -= 1
            while izq_start >= 0 and balance > 0:
                if tokens[izq_start] == ')': balance += 1
                elif tokens[izq_start] == '(': balance -= 1
                izq_start -= 1
            izq_start += 1
        else:
            if izq_start - 1 >= 0 and tokens[izq_start - 1] == '¬':
                izq_start -= 1
                
        der_end = idx + 1
        if tokens[der_end] == '¬':
            der_end += 1
        if tokens[der_end] == '(':
            balance = 1
            der_end += 1
            while der_end < len(tokens) and balance > 0:
                if tokens[der_end] == '(': balance += 1
                elif tokens[der_end] == ')': balance -= 1
                der_end += 1
        else:
            der_end += 1
            
        expr_izq = tokens[izq_start:idx]
        expr_der = tokens[idx + 1:der_end]
        sub_combinada = ['(', '('] + expr_izq + [')', '==', '('] + expr_der + [')', ')']
        tokens = tokens[:izq_start] + sub_combinada + tokens[der_end:]

    # 5. Reemplazo por operadores lógicos booleanos nativos e instantáneos de Python
    final_str = "".join(tokens)
    final_str = final_str.replace('¬', ' not ').replace('∧', ' and ').replace('∨', ' or ').replace('⊕', ' != ')
    return final_str

def extraer_variables(expr: str) -> list:
    return sorted(list(set(re.findall(r'[p-u]', expr))))

def generar_tabla(expr_raw: str):
    if not expr_raw:
        return [], []
        
    variables_detectadas = extraer_variables(expr_raw)
    if not variables_detectadas:
        return [], []
        
    expr_python = traducir_a_python(expr_raw)
    tabla = []
    
    # Generar permutaciones binarias ordenadas matemáticamente (1s arriba y 0s abajo)
    for valores in product([True, False], repeat=len(variables_detectadas)):
        entorno = dict(zip(variables_detectadas, valores))
        try:
            resultado = eval(expr_python, {"__builtins__": {}}, entorno)
            fila = [1 if v else 0 for v in valores] + [1 if resultado else 0]
            tabla.append(fila)
        except Exception:
            return [], []
            
    return variables_detectadas, tabla


# --- Renderizado de Resultados ---
with col_gen:
    btn_generar = st.button("📊 Generar", type="primary", use_container_width=True)

if btn_generar:
    expr_limpia = st.session_state.expr.replace(" ", "").strip()
    if not expr_limpia:
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_det, tabla_det = generar_tabla(expr_limpia)
        
        if not vars_det or not tabla_det:
            st.error("❌ Expresión inválida o error en la sintaxis de conectores.")
        else:
            cols_df = vars_det + ["Resultado"]
            df = pd.DataFrame(tabla_det, columns=cols_df)
            
            st.success(f"🎰 Tabla generada exitosamente para {len(vars_det)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
