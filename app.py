import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered", page_icon="🧮")

# --- Inyección de CSS para Fondo Negro Estricto ---
st.markdown(
    """
    <style>
    /* Fondo principal de la app */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    /* Estilos adicionales para textos y inputs en fondo oscuro */
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
    }
    /* Asegurar visibilidad del campo de texto */
    .stTextInput input {
        color: #ffffff !important;
        background-color: #1e1e1e !important;
        border: 1px solid #333333 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Título actualizado con el nombre del grupo
st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")
st.markdown("Construye tu expresión haciendo clic o editándola. El resultado se mostrará *exclusivamente en 0 y 1*.")

# --- Estado de la Sesión ---
if 'expr' not in st.session_state:
    st.session_state.expr = ""

# --- UI: Constructor de Expresión ---
st.subheader("🛠️ Constructor de Expresión")

cols = st.columns(6)
variables = ["p", "q", "r", "s", "t", "u"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f"{v}"

st.markdown("---")

st.subheader("➕ Operadores")

cols_op = st.columns(5)
operadores = ["∧", "∨", "¬", "->", "<->", "(", ")", "Espacio"]
for i, op in enumerate(operadores):
    with cols_op[i % 5]:
        if st.button(f"{op}", key=f"btn_{op}", use_container_width=True):
            if op == "NOT":
                st.session_state.expr += " NOT "
            elif op in ("(", ")"):
                st.session_state.expr += f"{op}"
            elif op == "Espacio":
                st.session_state.expr += " "
            else:
                st.session_state.expr += f" {op} "

col_limpiar, col_preview = st.columns(2)

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    st.session_state.expr = st.text_input("Expresión actual:", value=st.session_state.expr)

# --- Lógica Central ---
def normalizar_expresion(expr: str) -> str:
    """Traduce los operadores lógicos tradicionales a operadores válidos de Python."""
    e = expr.strip().upper()
    e = re.sub(r'\bAND\b', ' and ', e)
    e = re.sub(r'\bOR\b', ' or ', e)
    e = re.sub(r'\bNOT\b', ' not ', e)
    e = re.sub(r'\bXOR\b', ' ^ ', e)
    
    e = e.replace('<->', ' == ').replace('->', ' <= ')
    
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    """Detecta las variables únicas presentes en la expresión."""
    return sorted(list(set(re.findall(r'\b[A-F]\b', expr.upper()))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return None, "La expresión está vacía."
        
    expr_norm = normalizar_expresion(expr_raw)
    variables_detectadas = extraer_variables(expr_raw)
    
    if not variables_detectadas:
        return None, "No se detectaron variables válidas (A-F) en la expresión."
        
    tabla = []
    
    for valores in product([0, 1], repeat=len(variables_detectadas)):
        entorno = {v: bool(val) for v, val in zip(variables_detectadas, valores)}
        try:
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            fila = list(valores) + [1 if bool(resultado) else 0]
            tabla.append(fila)
        except Exception:
            return None, "Error de sintaxis en la expresión lógica. Revisa los paréntesis u operadores."
            
    return variables_detectadas, tabla

# --- Ejecución ---
st.markdown("---")
if st.button("🚀 Generar Tabla de la Verdad", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_resultado, tabla_resultado = generar_tabla(st.session_state.expr)
        
        if vars_resultado is None:
            st.error(f"❌ {tabla_resultado}")
        else:
            cols_df = vars_resultado + ["Resultado"]
            df = pd.DataFrame(tabla_resultado, columns=cols_df)
            
            st.success(f"✅ Tabla generada exitosamente para {len(vars_resultado)} variable(s).")
            
            df = df.astype(int)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Tabla en CSV", csv, "tabla_verdad.csv", "text/csv", use_container_width=True)
