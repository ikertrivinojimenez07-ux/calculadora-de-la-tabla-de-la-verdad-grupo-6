import streamlit as st
import ast
from itertools import product
import pandas as pd
import re

st.set_page_config(page_title="Calculadora Tabla de la Verdad - Grupo 6", layout="centered", page_icon="🧮")

# --- Inyección de CSS Corregida ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stApp li {
        color: #ffffff !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 28px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #aaaaaa !important;
    }
    .stTextInput input {
        color: #ffffff !important;
        background-color: #1e1e1e !important;
        border: 1px solid #333333 !important;
        font-size: 18px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🧮 Calculadora de Tabla de la Verdad - Grupo 6")

# --- Sección de Indicaciones ---
with st.expander("📖 INDICACIONES Y JERARQUÍA LÓGICA", expanded=False):
    st.markdown("""
    ### **Pasos para utilizar la calculadora:**
    1. **Construye tu fórmula:** Haz clic en las variables ($p, q, r...$) y los conectores o signos de agrupación.
    2. **Edición manual:** Si lo prefieres, puedes escribir o corregir la expresión directamente en el cuadro de texto usando los mismos símbolos.
    3. **Generación:** Haz clic en el botón verde **"🚀 Generar Tabla de la Verdad"**.
    
    ### **Significados de los Símbolos:**
    * **`¬`** : Negación (not)
    * **`∧`** : Conjunción (and)
    * **`∨`** : Disyunción (or)
    * **`→`** : Condicional (Implicación)
    * **`↔`** : Bicondicional (Doble Implicación)
    * **`( )`, `[ ]`, `{ }`** : Signos de agrupación
    """)

# --- Estado de la Sesión ---
if 'expr' not in st.session_state:
    st.session_state.expr = ""

# --- UI ---
st.subheader("🛠️ Variables")
cols = st.columns(6)
variables = ["p", "q", "r", "s", "t", "u"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f"{v}"

st.markdown("---")
st.subheader("➕ Conectores y Signos de Agrupación")
simbolos = ["¬", "∧", "∨", "→", "↔", "(", ")", "[", "]", "{", "}"]

cols_op = st.columns(6)
for i, sym in enumerate(simbolos):
    with cols_op[i % 6]:
        if st.button(sym, key=f"btn_op_{i}", use_container_width=True):
            st.session_state.expr += f"{sym}"

st.markdown("---")
col_limpiar, col_preview = st.columns(2)

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    st.session_state.expr = st.text_input("Expresión actual:", value=st.session_state.expr)

# --- EVALUADOR Y PARSER REESCRITO DESDE CERO ---
def evaluar_nodo(nodo, entorno):
    """Evalúa de manera recursiva el árbol sintáctico abstracto aplicando las reglas formales de la lógica."""
    if isinstance(nodo, ast.Expression):
        return evaluar_nodo(nodo.body, entorno)
    
    if isinstance(nodo, ast.Name):
        return entorno[nodo.id]
    
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.Not):
        return not evaluar_nodo(nodo.operand, entorno)
    
    if isinstance(nodo, ast.BoolOp):
        valores = [evaluar_nodo(val, entorno) for val in nodo.values]
        if isinstance(nodo.op, ast.And):
            return all(valores)
        if isinstance(nodo.op, ast.Or):
            return any(valores)
            
    if isinstance(nodo, ast.Compare):
        izq = evaluar_nodo(nodo.left, entorno)
        der = evaluar_nodo(nodo.comparators[0], entorno)
        op = nodo.ops[0]
        
        if isinstance(op, ast.Eq):  # Bicondicional (↔)
            return izq == der
        if isinstance(op, ast.LtE): # Condicional (→) traducido como <=
            return (not izq) or der

    raise ValueError("Estructura sintáctica no soportada o inválida.")

def normalizar_expresion(expr: str) -> str:
    """Traduce la cadena matemática a componentes entendibles por el parser de árbol de Python."""
    e = expr.strip()
    e = e.replace('[', '(').replace(']', ')')
    e = e.replace('{', '(').replace('}', ')')
    
    # Mapeo a tokens internos estables para la compilación sintáctica
    e = e.replace('¬', ' not ')
    e = e.replace('∧', ' and ')
    e = e.replace('∨', ' or ')
    e = e.replace('↔', ' == ')
    e = e.replace('→', ' <= ')
    
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    encontradas = set(re.findall(r'\b[p-u]\b', expr))
    orden_ui = ["p", "q", "r", "s", "t", "u"]
    return [v for v in orden_ui if v in encontradas]

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return None, "La expresión está vacía."
        
    expr_norm = normalizar_expresion(expr_raw)
    variables_detectadas = extraer_variables(expr_raw)
    
    if not variables_detectadas:
        return None, "No se detectaron variables válidas (p-u)."
        
    try:
        # Compilar la expresión en un árbol sintáctico abstracto (AST) seguro
        arbol = ast.parse(expr_norm, mode='eval')
    except Exception:
        return None, "Error de sintaxis. Revisa el orden de tus conectores o agrupaciones."
        
    tabla = []
    for valores in product([0, 1], repeat=len(variables_detectadas)):
        entorno = {v: bool(val) for v, val in zip(variables_detectadas, valores)}
        try:
            resultado = evaluar_nodo(arbol, entorno)
            fila = list(valores) + [1 if bool(resultado) else 0]
            tabla.append(fila)
        except Exception:
            return None, "Error al evaluar la combinación de conectores."
            
    return variables_detectadas, tabla

# --- Renderizado ---
st.markdown("---")
if st.button("🚀 Generar Tabla de la Verdad", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Construye una expresión primero.")
    else:
        vars_resultado, tabla_resultado = generar_tabla(st.session_state.expr)
        
        if vars_resultado is None:
            st.error(f"❌ {tabla_resultado}")
        else:
            cols_df = vars_resultado + ["Resultado"]
            df = pd.DataFrame(tabla_resultado, columns=cols_df)
            
            st.success("✅ Tabla generada exitosamente.")
            df = df.astype(int)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Estadísticas precisas basadas en los resultados generados
            total_variables = len(vars_resultado)
            total_verdades = int((df["Resultado"] == 1).sum())
            total_falsedades = int((df["Resultado"] == 0).sum())
            
            st.markdown("### 📊 Resumen de la Expresión")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Variables Utilizadas", value=total_variables)
            with col2:
                st.metric(label="Total de Verdades (1)", value=total_verdades)
            with col3:
                st.metric(label="Total de Falsedades (0)", value=total_falsedades)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.markdown("---")
            st.download_button("📥 Descargar Tabla en CSV", csv, "tabla_verdad.csv", "text/csv", use_container_width=True)
