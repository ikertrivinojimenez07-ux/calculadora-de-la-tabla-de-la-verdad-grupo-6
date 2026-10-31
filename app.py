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
    h1, h2, h3, p, span, label, li {
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

# --- Sección de Indicaciones ---
with st.expander("📖 INDICACIONES Y JERARQUÍA LÓGICA", expanded=False):
    st.markdown("""
    ### **Pasos para utilizar la calculadora:**
    1. **Construye tu fórmula:** Haz clic en las variables ($P, Q, R...$) y los conectores o signos de agrupación.
    2. **Edición manual:** Si lo prefieres, puedes escribir o corregir la expresión directamente en el cuadro de texto **"Expresión actual"**.
    3. **Generación:** Haz clic en el botón verde **"🚀 Generar Tabla de la Verdad"**.
    4. **Descarga:** Exporta tu tabla resuelta en formato CSV presionando **"📥 Descargar Tabla en CSV"**.
    
    ### **Significados de los Símbolos:**
    * **`¬`** : Negación
    * **`∧`** : Conjunción
    * **`∨`** : Disyunción
    * **`→`** : Condicional (Implicación)
    * **`↔`** : Bicondicional (Doble Implicación)
    * **`( )`, `[ ]`, `{ }`** : Signos de agrupación (Paréntesis, Corchetes y Llaves)
    """)

# --- Estado de la Sesión ---
if 'expr' not in st.session_state:
    st.session_state.expr = ""

# --- UI: Constructor de Expresión (Variables P-U) ---
st.subheader("🛠️ Variables")

cols = st.columns(6)
variables = ["P", "Q", "R", "S", "T", "U"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f"{v}"

st.markdown("---")

# --- UI: Conectores y Signos de Agrupación ---
st.subheader("➕ Conectores y Signos de Agrupación")

# Mapeo visual estricto de símbolos puros a los tokens internos de procesamiento
diccionario_operadores = {
    "¬": " NOT ",
    "∧": " AND ",
    "∨": " OR ",
    "→": " -> ",
    "↔": " <-> ",
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    "{": "{",
    "}": "}"
}

cols_op = st.columns(6)
for i, (nombre_visual, valor_interno) in enumerate(diccionario_operadores.items()):
    with cols_op[i % 6]:
        if st.button(nombre_visual, key=f"btn_op_{i}", use_container_width=True):
            st.session_state.expr += valor_interno

st.markdown("---")
col_limpiar, col_preview = st.columns(2)

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    st.session_state.expr = st.text_input("Expresión actual:", value=st.session_state.expr)

# --- Lógica Central ---
def normalizar_expresion(expr: str) -> str:
    """Traduce los símbolos formales y de agrupación a operadores lógicos de Python."""
    e = expr.strip().upper()
    
    # Normalizar corchetes y llaves a paréntesis estándar de Python
    e = e.replace('[', '(').replace(']', ')')
    e = e.replace('{', '(').replace('}', ')')
    
    # Reemplazar operadores lógicos
    e = re.sub(r'\bAND\b', ' and ', e)
    e = re.sub(r'\bOR\b', ' or ', e)
    e = re.sub(r'\bNOT\b', ' not ', e)
    
    # Condicionales e Implicaciones
    e = e.replace('<->', ' == ').replace('->', ' <= ')
    
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    """Detecta las variables únicas presentes en la expresión (Rango P-U)."""
    return sorted(list(set(re.findall(r'\b[P-U]\b', expr.upper()))))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return None, "La expresión está vacía."
        
    expr_norm = normalizar_expresion(expr_raw)
    variables_detectadas = extraer_variables(expr_raw)
    
    if not variables_detectadas:
        return None, "No se detectaron variables válidas (P-U) en la expresión."
        
    tabla = []
    
    for valores in product([0, 1], repeat=len(variables_detectadas)):
        entorno = {v: bool(val) for v, val in zip(variables_detectadas, valores)}
        try:
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            fila = list(valores) + [1 if bool(resultado) else 0]
            tabla.append(fila)
        except Exception:
            return None, "Error de sintaxis en la expresión lógica. Revisa tus signos de agrupación o conectores."
            
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
