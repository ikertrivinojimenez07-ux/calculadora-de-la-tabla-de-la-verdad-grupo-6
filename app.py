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

# Lista global renombrada para evitar conflictos con variables internas
VARIABLES_DISPONIBLES = ["p", "q", "r", "s", "t", "u"]
cols_vars = st.columns(6)

for i, v in enumerate(VARIABLES_DISPONIBLES):
    with cols_vars[i]:
        if st.button(v, key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

st.markdown("---")

st.subheader("➕ Operadores")

# Lista con solo los símbolos solicitados
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


# --- Motor de Evaluación Lógica (Parser AST) ---
class LogicaParser:
    """Analizador sintáctico recursivo para evaluar expresiones lógicas con precedencia matemática."""
    def __init__(self, tokens, valores_variables):
        self.tokens = tokens
        self.valores = valores_variables
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def get(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self):
        try:
            return self.eval_bicondicional()
        except Exception:
            return False

    def eval_bicondicional(self):
        nodo = self.eval_implicacion()
        while self.peek() == "↔":
            self.get()
            derecho = self.eval_implicacion()
            nodo = (nodo == derecho)
        return nodo

    def eval_implicacion(self):
        nodo = self.eval_operadores_base()
        if self.peek() == "→":
            self.get()
            derecho = self.eval_implicacion()
            nodo = (not nodo) or derecho
        return nodo

    def eval_operadores_base(self):
        nodo = self.eval_factor()
        while self.peek() in ("∧", "∨", "⊕"):
            op = self.get()
            derecho = self.eval_factor()
            if op == "∧":
                nodo = nodo and derecho
            elif op == "∨":
                nodo = nodo or derecho
            elif op == "⊕":
                nodo = nodo != derecho
        return nodo

    def eval_factor(self):
        tok = self.peek()
        if tok == "¬":
            self.get()
            return not self.eval_factor()
        
        if tok in ("(", "[", "{"):
            apertura = self.get()
            cierre_esperado = ")" if apertura == "(" else "]" if apertura == "[" else "}"
            resultado = self.parse()
            if self.peek() == cierre_esperado:
                self.get()
            return resultado

        if tok in self.valores:
            self.get()
            return self.valores[tok]

        return False


def extraer_variables(expr: str) -> list:
    return sorted(list(set(re.findall(r'\b[p-u]\b', expr))))

def evaluar_expresion_robusta(expr_raw: str, valores_variables: dict) -> bool:
    tokens = re.findall(r'¬|∧|∨|⊕|→|↔|\(|\)|\[|\]|\{|\}|[p-u]', expr_raw)
    parser = LogicaParser(tokens, valores_variables)
    return parser.parse()

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
        
    variables_detectadas = extraer_variables(expr_raw)
    if not variables_detectadas:
        return [], []
        
    tabla = []
    
    for valores in product([True, False], repeat=len(variables_detectadas)):
        entorno = dict(zip(variables_detectadas, valores))
        try:
            resultado = evaluar_expresion_robusta(expr_raw, entorno)
            fila = [1 if v else 0 for v in valores] + [1 if resultado else 0]
            tabla.append(fila)
        except Exception:
            return [], []
            
    return variables_detectadas, tabla


# --- Ejecución ---
with col_gen:
    btn_generar = st.button("📊 Generar", type="primary", use_container_width=True)

if btn_generar:
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_det, tabla_det = generar_tabla(st.session_state.expr)
        
        if not vars_det or not tabla_det:
            st.error("❌ Expresión inválida. Revisa el orden de los operadores y paréntesis.")
        else:
            cols_df = vars_det + ["Resultado"]
            df = pd.DataFrame(tabla_det, columns=cols_df)
            
            st.success(f"🎰 Tabla generada exitosamente para {len(vars_det)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
