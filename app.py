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

# --- Lógica Central Robusta ---
def normalizar_expresion(expr: str) -> str:
    """Convierte de forma segura una expresión lógica a sintaxis pura de Python."""
    e = expr.strip()
    # 1. Homologar delimitadores visuales a paréntesis ordinarios
    e = e.replace('[', '(').replace(']', ')')
    e = e.replace('{', '(').replace('}', ')')
    
    # 2. Tokenizar la expresión de forma precisa
    tokens = re.findall(r'\(|\)|¬|∧|∨|⊕|→|↔|[p-u]', e)
    
    def evaluar_tokens(tks):
        """Función interna recursiva para reescribir prioridades de → y ↔ de adentro hacia afuera."""
        # Resolver subexpresiones dentro de paréntesis primero
        while '(' in tks:
            start = -1
            end = -1
            # Encontrar el par de paréntesis interno más profundo
            for idx, tk in enumerate(tks):
                if tk == '(':
                    start = idx
                elif tk == ')':
                    end = idx
                    break
            if start != -1 and end != -1:
                sub_res = evaluar_tokens(tks[start + 1:end])
                tks = tks[:start] + ['('] + sub_res + [')'] + tks[end + 1:]
            else:
                break

        # Resolver Implicaciones (→) de derecha a izquierda (asociatividad derecha)
        while '→' in tks:
            # Buscamos el último para evaluar correctamente la jerarquía
            idx = len(tks) - 1 - tks[::-1].index('→')
            
            # Buscar el operando izquierdo de la implicación
            izq_start = idx - 1
            if tks[izq_start] == ')':
                balance = 1
                izq_start -= 1
                while izq_start >= 0 and balance > 0:
                    if tks[izq_start] == ')': balance += 1
                    elif tks[izq_start] == '(': balance -= 1
                    izq_start -= 1
                izq_start += 1
            else:
                # Si viene precedido por una negación, arrastrarla
                if izq_start - 1 >= 0 and tks[izq_start - 1] == '¬':
                    izq_start -= 1
            
            # Buscar el operando derecho de la implicación
            der_end = idx + 1
            if tks[der_end] == '¬':
                der_end += 1
            if tks[der_end] == '(':
                balance = 1
                der_end += 1
                while der_end < len(tks) and balance > 0:
                    if tks[der_end] == '(': balance += 1
                    elif tks[der_end] == ')': balance -= 1
                    der_end += 1
            else:
                der_end += 1
                
            expr_izq = tks[izq_start:idx]
            expr_der = tks[idx + 1:der_end]
            
            # Reemplazar con la equivalencia condicional de Python: not A or B
            nueva_sub = ['(', '¬'] + expr_izq + [')', '∨', '('] + expr_der + [']']
            tks = tks[:izq_start] + nueva_sub + tks[der_end:]

        # Resolver Equivalencias (↔)
        while '↔' in tks:
            idx = tks.index('↔')
            
            izq_start = idx - 1
            if tks[izq_start] == ')':
                balance = 1
                izq_start -= 1
                while izq_start >= 0 and balance > 0:
                    if tks[izq_start] == ')': balance += 1
                    elif tks[izq_start] == '(': balance -= 1
                    izq_start -= 1
                izq_start += 1
            else:
                if izq_start - 1 >= 0 and tks[izq_start - 1] == '¬':
                    izq_start -= 1
                    
            der_end = idx + 1
            if tks[der_end] == '¬':
                der_end += 1
            if tks[der_end] == '(':
                balance = 1
                der_end += 1
                while der_end < len(tks) and balance > 0:
                    if tks[der_end] == '(': balance += 1
                    elif tks[der_end] == ')': balance -= 1
                    der_end += 1
            else:
                der_end += 1
                
            expr_izq = tks[izq_start:idx]
            expr_der = tks[idx + 1:der_end]
            
            nueva_sub = ['('] + expr_izq + [')', '==', '('] + expr_der + [')']
            tks = tks[:izq_start] + nueva_sub + tks[der_end:]
            
        return tks

    # Ejecutar la estructuración recursiva
    tokens_procesados = evaluar_tokens(tokens)
    final_expr = " ".join(tokens_procesados)
    
    # 3. Mapeo final a palabras reservadas lógicas de Python
    final_expr = final_expr.replace('[', '(').replace(']', ')')
    final_expr = re.sub(r'¬', ' not ', final_expr)
    final_expr = re.sub(r'∧', ' and ', final_expr)
    final_expr = re.sub(r'∨', ' or ', final_expr)
    final_expr = re.sub(r'⊕', ' != ', final_expr)
    
    return final_expr

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
    
    # Permutaciones lógicas estándar (True/False)
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
            st.error("❌ Expresión inválida o matemática incorrecta.")
        else:
            cols_df = vars_det + ["Resultado"]
            df = pd.DataFrame(tabla_det, columns=cols_df)
            
            st.success(f"🎰 Tabla generada para {len(vars_det)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
