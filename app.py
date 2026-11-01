
import re
from itertools import product

import pandas as pd
import streamlit as st


# ==========================================
# CONFIGURACION DE LA APLICACION
# ==========================================

st.set_page_config(
    page_title="Calculadora de Tabla de Verdad",
    page_icon="🔢",
    layout="centered"
)

st.title("🔢 Calculadora de Tabla de Verdad")

st.write(
    "Construye expresiones lógicas utilizando las variables "
    "p, q, r, s, t y u. Los resultados se mostrarán en 0 y 1."
)

VARIABLES = ["p", "q", "r", "s", "t", "u"]

if "expr" not in st.session_state:
    st.session_state.expr = ""


# ==========================================
# FUNCIONES PARA INSERTAR Y LIMPIAR
# ==========================================

def insertar(texto):
    actual = st.session_state.expr

    separador = "" if not actual or actual.endswith(" ") else " "

    st.session_state.expr = actual + separador + texto + " "


def limpiar():
    st.session_state.expr = ""


# ==========================================
# CONSTRUCTOR DE VARIABLES
# ==========================================

st.subheader("✍️ Constructor de expresión")

cols = st.columns(6)

for i, variable in enumerate(VARIABLES):

    with cols[i]:

        st.button(
            variable,
            key=f"variable_{variable}",
            width="stretch",
            on_click=insertar,
            args=(variable,)
        )


# ==========================================
# OPERADORES LOGICOS
# ==========================================

st.subheader("Operadores lógicos")

st.caption(
    "∧ Conjunción | ∨ Disyunción | ¬ Negación | "
    "→ Condicional o implicación | ↔ Bicondicional"
)

operadores = [
    ("∧", "∧"),
    ("∨", "∨"),
    ("¬", "¬"),
    ("→", "→"),
    ("↔", "↔"),
    ("(", "("),
    (")", ")")
]

cols_op = st.columns(4)

for i, (nombre, simbolo) in enumerate(operadores):

    with cols_op[i % 4]:

        st.button(
            nombre,
            key=f"operador_{i}",
            width="stretch",
            on_click=insertar,
            args=(simbolo,)
        )


# ==========================================
# EXPRESION LOGICA
# ==========================================

st.subheader("Expresión construida")

st.text_input(
    "Escribe o modifica tu expresión:",
    key="expr",
    placeholder="Ejemplo: (p ∧ q) → ¬r"
)

st.button(
    "🗑️ Limpiar expresión",
    width="stretch",
    on_click=limpiar
)


# ==========================================
# RECONOCIMIENTO DE SIMBOLOS
# ==========================================

def tokenizar(expresion):

    patron = re.compile(
        r"\s*(<->|->|[p-u]|[∧∨¬→↔()])"
    )

    equivalencias = {
        "∧": "AND",
        "∨": "OR",
        "¬": "NOT",
        "→": "IMPLICA",
        "->": "IMPLICA",
        "↔": "BICONDICIONAL",
        "<->": "BICONDICIONAL"
    }

    tokens = []
    posicion = 0

    while posicion < len(expresion):

        if expresion[posicion:].strip() == "":
            break

        coincidencia = patron.match(
            expresion,
            posicion
        )

        if coincidencia is None:

            raise ValueError(
                f"Símbolo no reconocido: "
                f"{expresion[posicion:posicion+12]}"
            )

        token = coincidencia.group(1)

        tokens.append(
            equivalencias.get(token, token)
        )

        posicion = coincidencia.end()

    return tokens


# ==========================================
# EVALUACION DE EXPRESIONES LOGICAS
# ==========================================

def evaluar_expresion(expresion, entorno):

    tokens = tokenizar(expresion)

    if not tokens:
        raise ValueError("Debes escribir una expresión lógica.")

    posicion = 0

    def consumir(esperado=None):

        nonlocal posicion

        if posicion >= len(tokens):
            raise ValueError("La expresión está incompleta.")

        token = tokens[posicion]

        if esperado is not None and token != esperado:

            raise ValueError(
                f"Se esperaba {esperado}."
            )

        posicion += 1

        return token

    # PROPOSICIONES Y PARENTESIS

    def atomico():

        token = consumir()

        if token in entorno:
            return entorno[token]

        if token == "(":

            resultado = bicondicional()

            consumir(")")

            return resultado

        raise ValueError(
            f"Elemento lógico inválido: {token}"
        )

    # NEGACION

    def negacion():

        if (
            posicion < len(tokens)
            and tokens[posicion] == "NOT"
        ):

            consumir("NOT")

            return not negacion()

        return atomico()

    # CONJUNCION

    def conjuncion():

        resultado = negacion()

        while (
            posicion < len(tokens)
            and tokens[posicion] == "AND"
        ):

            consumir("AND")

            derecha = negacion()

            resultado = resultado and derecha

        return resultado

    # DISYUNCION

    def disyuncion():

        resultado = conjuncion()

        while (
            posicion < len(tokens)
            and tokens[posicion] == "OR"
        ):

            consumir("OR")

            derecha = conjuncion()

            resultado = resultado or derecha

        return resultado

    # CONDICIONAL O IMPLICACION

    def condicional():

        izquierda = disyuncion()

        if (
            posicion < len(tokens)
            and tokens[posicion] == "IMPLICA"
        ):

            consumir("IMPLICA")

            derecha = condicional()

            return (not izquierda) or derecha

        return izquierda

    # BICONDICIONAL

    def bicondicional():

        resultado = condicional()

        while (
            posicion < len(tokens)
            and tokens[posicion] == "BICONDICIONAL"
        ):

            consumir("BICONDICIONAL")

            derecha = condicional()

            resultado = resultado == derecha

        return resultado

    resultado = bicondicional()

    if posicion < len(tokens):

        raise ValueError(
            f"Expresión incorrecta cerca de {tokens[posicion]}."
        )

    return resultado


# ==========================================
# GENERACION DE TABLA DE VERDAD
# ==========================================

def generar_tabla(expresion):

    tokens = tokenizar(expresion)

    variables_usadas = [
        variable
        for variable in VARIABLES
        if variable in tokens
    ]

    if not variables_usadas:

        raise ValueError(
            "No se encontraron variables entre p y u."
        )

    tabla = []

    # GENERAR COMBINACIONES DE 0 Y 1

    for valores in product(
        [0, 1],
        repeat=len(variables_usadas)
    ):

        entorno = {
            variable: bool(valor)
            for variable, valor in zip(
                variables_usadas,
                valores
            )
        }

        resultado = evaluar_expresion(
            expresion,
            entorno
        )

        fila = list(valores) + [
            int(resultado)
        ]

        tabla.append(fila)

    return variables_usadas, tabla


# ==========================================
# EJECUCION DE LA APLICACION
# ==========================================

if st.button(
    "📝 Generar tabla de verdad",
    type="primary",
    width="stretch"
):

    try:

        variables_usadas, tabla = generar_tabla(
            st.session_state.expr
        )

        columnas = variables_usadas + [
            "Resultado"
        ]

        df = pd.DataFrame(
            tabla,
            columns=columnas
        )

        st.success(
            f"✅ Tabla generada correctamente. "
            f"Se utilizaron {len(variables_usadas)} variables."
        )

        st.subheader("Tabla de verdad")

        st.dataframe(
            df,
            width="stretch",
            hide_index=True
        )

        # DESCARGAR RESULTADOS

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="📥 Descargar tabla en CSV",
            data=csv,
            file_name="tabla_de_verdad.csv",
            mime="text/csv",
            width="stretch"
        )

    except ValueError as error:

        st.error(f"❌ Error: {error}")


# ==========================================
# INFORMACION FINAL
# ==========================================

st.divider()

st.caption(
    "El condicional y la implicación utilizan el símbolo →. "
    "El bicondicional utiliza el símbolo ↔."
)
