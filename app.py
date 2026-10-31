import streamlit as st
from itertools import product
import pandas as pd
import re

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered")

# --- Título Principal ---
st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")
st.markdown("Construye tu expresión haciendo clic en los botones o escribiéndola manualmente abajo.")

# --- Inicialización del Estado de Sesión ---
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

operadores = ["¬", "∧", "∨", "⊕", "→", "↔", "(", ")", "[", "]", "{", "}"]
cols_ops = st.columns(4)

for i, simbolo in enumerate(operadores):
    with cols_ops[i % 4]:
        if st.button(simbolo, key=f"btn_sym_{i}", use_container_width=True):
            st.session_state.expr += f"{simbolo}"

st.markdown("---")

# Caja de texto limpia para prevenir bucles de refresco reactivo infinito
expr_actual = st.text_input("📝 Expresión actual (puedes editarla o teclearla directamente aquí):", value=st.session_state.expr)
st.session_state.expr = expr_actual

col_limpiar, col_gen = st.columns(2)

with col_limpiar:
    if st.button("🗑️ Limpiar Todo", type="secondary", use_container_width=True):
        st.session_state.expr = ""
        # Usamos fallback seguro en lugar de st.rerun() para evitar congelamiento de la UI
        st.write("Presiona 'Generar Tabla' para limpiar resultados de pantalla.")

# --- Motor Matemático de Conversión Seguro ---
def traducir_a_python(expr: str) -> str:
    # 1. Homologar delimitadores de agrupación a formato uniforme
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
        if der_end < len(tokens) and tokens[der_end] == '¬':
            der_end += 1
        if der_end < len(tokens) and tokens[der_end] == '(':
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
        if der_end < len(tokens) and tokens[der_end] == '¬':
            der_end += 1
        if der_end < len(tokens) and tokens[der_end] == '(':
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

    final_str = "".join(tokens)
    final_str = final_str.replace('¬', ' not ').replace('∧', ' and ').replace('∨', ' or ').replace('⊕', ' != ')
    return final_str

def extraer_variables(expr: str) -> list:
    return sorted(list(set(re.findall(r'[p-u]', expr))))

def generar_tabla(expr_raw: str):
    # Remover espacios vacíos para asegurar el análisis preciso de tokens
    expr_limpia = expr_raw.replace(" ", "")
    if not expr_limpia:
        return [], []
        
    variables_detectadas = extraer_variables(expr_limpia)
    if not variables_detectadas:
        return [], []
        
    expr_python = traducir_a_python(expr_limpia)
    tabla = []
    
    # Permutaciones binarias discretas (Verdadero = 1, Falso = 0)
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
    btn_generar = st.button("📊 Generar Tabla", type="primary", use_container_width=True)

if btn_generar:
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_det, tabla_det = generar_tabla(st.session_state.expr)
        
        if not vars_det or not tabla_det:
            st.error("❌ Expresión inválida. Por favor revisa el orden de tus paréntesis o conectores lógicos.")
        else:
            cols_df = vars_det + ["Resultado"]
            df = pd.DataFrame(tabla_det, columns=cols_df)
            
            st.success(f"🎰 Tabla generada exitosamente para {len(vars_det)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
