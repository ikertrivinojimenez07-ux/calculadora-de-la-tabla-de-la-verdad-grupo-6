
import streamlit as st
import pandas as pd
import re
from itertools import product

# CONFIGURACIÓN DE LA APLICACIÓN
st.set_page_config(
    page_title="Calculadora de Tabla de Verdad-grupo 6",
    layout="centered"
)

st.title("🔢 Calculadora de Tabla de Verdad")
st.markdown(
    "Construye tu expresión lógica utilizando las variables "
    "p, q, r, s, t y u. El resultado se mostrará en 0 y 1."
)

# ESTADO DE LA SESIÓN
if "expr" not in st.session_state:
    st.session_state.expr = ""

# VARIABLES PROPOSICIONALES
st.subheader("✍️ Constructor de Expresión")

variables = ["p", "q", "r", "s", "t", "u"]

cols = st.columns(6)

for i, variable in enumerate(variables):
    with cols[i]:
        if st.button(
            variable,
            key=f"variable_{variable}",
            use_container_width=True
        ):
            st.session_state.expr += f" {variable} "

st.markdown("---")

# OPERADORES LÓGICOS
st.subheader("Operadores lógicos")

operadores = [
    ("∧", "and"),
    ("∨", "or"),
    ("¬", "not"),
    ("→", "->"),
    ("↔", "<->"),
    ("(", "("),
    (")", ")")
]

cols = st.columns(4)

for i, (nombre, simbolo) in enumerate(operadores):
    with cols[i % 4]:
        if st.button(
            nombre,
            key=f"operador_{i}",
            use_container_width=True
        ):
            st.session_state.expr += f" {simbolo} "

# LIMPIAR EXPRESIÓN
if st.button(
    "🗑️ Limpiar expresión",
    use_container_width=True
):
    st.session_state.expr = ""

# MOSTRAR EXPRESIÓN
st.subheader("Expresión construida")

st.text_input(
    "Escribe o modifica tu expresión lógica:",
    key="expr",
    placeholder="Ejemplo: (p ∧ q) → ¬r"
)

st.markdown("---")


# RECONOCIMIENTO DE SÍMBOLOS
def tokenizar(expr):

    patron = r"\s*(<->|->|[p-u]|[∧∨¬→↔()])"

    tokens = []
    posicion = 0

    while posicion < len(expr):

        if expr[posicion:].strip() == "":
            break

        coincidencia = re.match(
            patron,
            expr[posicion:]
        )

        if not coincidencia:
            raise ValueError(
                f"Símbolo no reconocido: {expr[posicion:]}"
            )

        tokens.append(coincidencia.group(1))
        posicion += coincidencia.end()

    equivalencias = {
        "∧": "AND",
        "∨": "OR",
        "¬": "NOT",
        "→": "IMPLICA",
        "↔": "BICONDICIONAL"
    }

    return [
        equivalencias.get(token, token)
        for token in tokens
    ]


# EVALUACIÓN DE EXPRESIONES LÓGICAS
def evaluar_expresion(expr, entorno):

    tokens = tokenizar(expr)
    posicion = 0

    def consumir(esperado=None):

        nonlocal posicion

        if posicion >= len(tokens):
            raise ValueError("Expresión incompleta.")

        token = tokens[posicion]

        if esperado is not None and token != esperado:
            raise ValueError(
                f"Se esperaba {esperado}."
            )

        posicion += 1
        return token

    # PROPOSICIONES Y PARÉNTESIS
    def atomico():

        token = consumir()

        if token in entorno:
            return entorno[token]

        if token == "(":
            resultado = bicondicional()
            consumir(")")
            return resultado

        raise ValueError(
            f"Proposición inválida: {token}"
        )

    # NEGACIÓN
    def negacion():

        if (
            posicion < len(tokens)
            and tokens[posicion] == "NOT"
        ):
            consumir("NOT")
            return not negacion()

        return atomico()

    # CONJUNCIÓN
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

    # DISYUNCIÓN
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

    # CONDICIONAL O IMPLICACIÓN
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

    if posicion != len(tokens):
        raise ValueError(
            f"Símbolo inesperado: {tokens[posicion]}"
        )

    return resultado


# GENERACIÓN DE LA TABLA DE VERDAD
def generar_tabla(expr):

    if not expr.strip():
        raise ValueError(
            "Debes ingresar una expresión lógica."
        )

    tokens = tokenizar(expr)

    variables_disponibles = [
        "p", "q", "r", "s", "t", "u"
    ]

    variables_usadas = [
        variable
        for variable in variables_disponibles
        if variable in tokens
    ]

    if not variables_usadas:
        raise ValueError(
            "No se encontraron variables lógicas."
        )

    tabla = []

    # GENERAR TODAS LAS COMBINACIONES DE 0 Y 1
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
            expr,
            entorno
        )

        fila = list(valores) + [
            int(resultado)
        ]

        tabla.append(fila)

    return variables_usadas, tabla


# BOTÓN PARA GENERAR LA TABLA
if st.button(
    "📝 Generar Tabla de Verdad",
    type="primary",
    use_container_width=True
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
            "✅ Tabla generada correctamente. "
            f"Se utilizaron {len(variables_usadas)} variable(s)."
        )

        # MOSTRAR TABLA
        st.subheader("Tabla de verdad")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # DESCARGAR TABLA
        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="📥 Descargar tabla en CSV",
            data=csv,
            file_name="tabla_de_verdad.csv",
            mime="text/csv"
        )

    except ValueError as error:

        st.error(f"❌ Error: {error}")

    except Exception as error:

        st.error(
            f"Se produjo un error: {error}"
        )
