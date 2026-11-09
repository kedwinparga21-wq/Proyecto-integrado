# -*- coding: utf-8 -*-
"""AE3 - Transformacion y enriquecimiento de datos (version script del notebook)."""
try:
    display
except NameError:
    display = print

import io
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 160)

# Rutas relativas: si el notebook está en AE3/notebooks usa AE3/; si no, crea ./AE3
if Path.cwd().name in ("notebooks", "src"):
    RAIZ = Path.cwd().parent
else:
    RAIZ = Path.cwd() / "AE3"

DIR_DATOS = RAIZ / "datos"
DIR_RESULTADOS = RAIZ / "resultados"
DIR_DOCUMENTO = RAIZ / "documento"
for carpeta in (DIR_DATOS, DIR_RESULTADOS, DIR_DOCUMENTO):
    carpeta.mkdir(parents=True, exist_ok=True)

print("Carpeta del proyecto:", RAIZ)

DATASET_ID = "infinite-dataset-hub/RetailSalesPerformance"
FUENTE = f"hf://datasets/{DATASET_ID}/data.csv"
FECHA_CONSULTA = dt.date.today().isoformat()

# Versión original, sin modificar, para comparar con la transformada
df_original = pd.read_csv(FUENTE)
df_original.to_csv(DIR_DATOS / "dataset_original.csv", index=False, encoding="utf-8")
df = df_original.copy()

print("Dataset:", DATASET_ID, "| consultado:", FECHA_CONSULTA)
print("Filas y columnas:", df.shape)
df.head()

# Estado inicial (antes de transformar)
estado_inicial = {
    "filas": len(df_original),
    "columnas": df_original.shape[1],
    "valores_nulos": int(df_original.isna().sum().sum()),
    "filas_duplicadas": int(df_original.duplicated().sum()),
}
print(estado_inicial)
pd.DataFrame({"tipo_original": df_original.dtypes.astype(str), "nulos": df_original.isna().sum()})

cambios = []

# 1) Tipos de datos: fecha y numéricos
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
n_fechas_ok = int(df["Date"].notna().sum())
n_fechas_mal = int(df["Date"].isna().sum())
cambios.append({
    "paso": "Convertir Date a fecha",
    "detalle": f"object -> datetime64 ({n_fechas_ok} válidas, {n_fechas_mal} inválidas)",
    "motivo": "Permite agrupar por mes y trimestre",
    "registros_afectados": n_fechas_ok,
})

for col in ["UnitsSold", "Revenue"]:
    nulos_antes = int(df[col].isna().sum())
    df[col] = pd.to_numeric(df[col], errors="coerce")
    nulos_nuevos = int(df[col].isna().sum()) - nulos_antes
    cambios.append({
        "paso": f"Validar {col} como numérico",
        "detalle": f"Conversión con pd.to_numeric ({nulos_nuevos} valores no numéricos pasaron a nulo)",
        "motivo": "Garantiza que las sumas y promedios sean correctos",
        "registros_afectados": nulos_nuevos,
    })

# 2) Normalizar texto de las categorías (espacios sobrantes)
cols_texto = ["OutletName", "Location", "ProductCategory", "CustomerAgeGroup", "CustomerIncomeLevel", "Label"]
modificados = 0
for col in cols_texto:
    original = df[col].astype("string")
    limpio = original.str.strip().str.replace(r"\s+", " ", regex=True)
    modificados += int((limpio != original).sum())
    df[col] = limpio
cambios.append({
    "paso": "Normalizar texto",
    "detalle": "Se quitaron espacios sobrantes en las columnas de texto",
    "motivo": "Evita que 'Food' y 'Food ' cuenten como categorías distintas",
    "registros_afectados": modificados,
})

# 3) Duplicados exactos (ignorando el identificador idx)
cols_sin_id = [c for c in df.columns if c != "idx"]
n_duplicados = int(df.duplicated(subset=cols_sin_id).sum())
df = df.drop_duplicates(subset=cols_sin_id).reset_index(drop=True)
cambios.append({
    "paso": "Revisar duplicados",
    "detalle": f"Filas idénticas (sin contar idx) eliminadas: {n_duplicados}",
    "motivo": "Un registro repetido duplicaría unidades e ingresos",
    "registros_afectados": n_duplicados,
})

# 4) Valores faltantes: se informan, no se imputan
nulos_clave = int(df[["Date", "UnitsSold", "Revenue"]].isna().any(axis=1).sum())
cambios.append({
    "paso": "Revisar valores faltantes",
    "detalle": "Nulos en Date, UnitsSold o Revenue (no se imputan; los cálculos los omiten)",
    "motivo": "Reemplazar sin criterio inventaría información",
    "registros_afectados": nulos_clave,
})

# 5) Valores no válidos: unidades o ingresos <= 0 (se reportan, no se borran)
n_no_validos = int(((df["UnitsSold"] <= 0) | (df["Revenue"] <= 0)).sum())
cambios.append({
    "paso": "Revisar valores no positivos",
    "detalle": "Registros con UnitsSold <= 0 o Revenue <= 0 (se conservan y se reportan)",
    "motivo": "Solo se calcula precio unitario cuando UnitsSold > 0",
    "registros_afectados": n_no_validos,
})

tabla_cambios = pd.DataFrame(cambios)
tabla_cambios

df["Anio"] = df["Date"].dt.year.astype("Int64")
df["Trimestre"] = df["Date"].dt.quarter.astype("Int64")
df["Mes"] = df["Date"].dt.strftime("%Y-%m")
df["DiaSemana"] = df["Date"].dt.day_name()
df["FinDeSemana"] = df["Date"].dt.dayofweek >= 5
df["PrecioUnitario"] = (df["Revenue"] / df["UnitsSold"].where(df["UnitsSold"] > 0)).round(2)
df["NivelVenta"] = pd.qcut(df["Revenue"].rank(method="first"), q=3, labels=["Bajo", "Medio", "Alto"])

diccionario_nuevas = pd.DataFrame([
    ["Anio", "Date.dt.year", "Año de la venta", "Agrupar por año"],
    ["Trimestre", "Date.dt.quarter", "Trimestre (1 a 4)", "Comparar periodos"],
    ["Mes", "Date.dt.strftime('%Y-%m')", "Mes de la venta (AAAA-MM)", "Responde P3"],
    ["DiaSemana", "Date.dt.day_name()", "Día de la semana", "Detectar patrones semanales"],
    ["FinDeSemana", "dayofweek >= 5", "Verdadero si es sábado o domingo", "Comparar fin de semana vs. entre semana"],
    ["PrecioUnitario", "Revenue / UnitsSold (si UnitsSold > 0)", "Ingreso medio por unidad", "Comparar precios entre categorías"],
    ["NivelVenta", "Terciles de Revenue (Bajo / Medio / Alto)", "Clasificación del tamaño de la venta", "Segmentar registros por ingreso"],
], columns=["variable", "formula_o_regla", "significado", "utilidad"])

print("Columnas finales:", list(df.columns))
diccionario_nuevas

# Comparación antes / después
estado_final = {
    "filas": len(df),
    "columnas": df.shape[1],
    "valores_nulos": int(df.isna().sum().sum()),
    "filas_duplicadas": int(df.duplicated(subset=[c for c in df.columns if c != "idx"]).sum()),
}
comparacion = pd.DataFrame({"antes": estado_inicial, "despues": estado_final})
print(comparacion)

tipos = pd.DataFrame({"tipo_antes": df_original.dtypes.astype(str)}).join(
    pd.DataFrame({"tipo_despues": df.dtypes.astype(str)}), how="outer")
tipos

def resumen_por(datos, columna):
    t = (datos.groupby(columna, observed=True)
              .agg(Registros=("idx", "count"), Unidades=("UnitsSold", "sum"), Ingresos=("Revenue", "sum"))
              .reset_index())
    t["Part_Unidades_%"] = (t["Unidades"] / t["Unidades"].sum() * 100).round(2)
    t["Part_Ingresos_%"] = (t["Ingresos"] / t["Ingresos"].sum() * 100).round(2)
    t["PrecioMedioUnidad"] = (t["Ingresos"] / t["Unidades"]).round(2)
    return t.sort_values("Ingresos", ascending=False).reset_index(drop=True)


def ordenar_por_lista(t, columna, orden):
    pos = {v: i for i, v in enumerate(orden)}
    t = t.copy()
    t["_o"] = t[columna].map(lambda v: pos.get(v, 99))
    return t.sort_values(["_o", columna]).drop(columns="_o").reset_index(drop=True)

# P1. Categorías de producto
p1_categorias = resumen_por(df, "ProductCategory")
p1_categorias

# P2. Tiendas y ubicaciones
p2_tiendas = resumen_por(df, "OutletName")
p2_ubicaciones = resumen_por(df, "Location")
display(p2_tiendas)
display(p2_ubicaciones)

# P3. Evolución mensual
p3_mensual = (df.dropna(subset=["Date"])
                .groupby("Mes")
                .agg(Registros=("idx", "count"), DiasConVentas=("Date", "nunique"),
                     Unidades=("UnitsSold", "sum"), Ingresos=("Revenue", "sum"))
                .reset_index().sort_values("Mes").reset_index(drop=True))
p3_mensual["IngresoMedioPorDia"] = (p3_mensual["Ingresos"] / p3_mensual["DiasConVentas"]).round(2)
p3_mensual["Var_Unidades_%"] = (p3_mensual["Unidades"].pct_change() * 100).round(2)
p3_mensual["Var_Ingresos_%"] = (p3_mensual["Ingresos"].pct_change() * 100).round(2)
p3_mensual

# P4. Segmentos de clientes
p4_edad = resumen_por(df, "CustomerAgeGroup")
p4_edad["_ini"] = p4_edad["CustomerAgeGroup"].str.extract(r"(\d+)")[0].astype(float)
p4_edad = p4_edad.sort_values("_ini").drop(columns="_ini").reset_index(drop=True)

p4_ingreso = ordenar_por_lista(resumen_por(df, "CustomerIncomeLevel"),
                               "CustomerIncomeLevel", ["Low", "Medium", "High"])
display(p4_edad)
display(p4_ingreso)

tablas = {
    "p1_categorias": (p1_categorias, "ProductCategory"),
    "p2_tiendas": (p2_tiendas, "OutletName"),
    "p2_ubicaciones": (p2_ubicaciones, "Location"),
    "p3_mensual": (p3_mensual, "Mes"),
    "p4_edad": (p4_edad, "CustomerAgeGroup"),
    "p4_ingreso": (p4_ingreso, "CustomerIncomeLevel"),
}

filas = []
for nombre, (t, col) in tablas.items():
    base = df.dropna(subset=[col])
    ok_u = bool(np.isclose(t["Unidades"].sum(), base["UnitsSold"].sum()))
    ok_i = bool(np.isclose(t["Ingresos"].sum(), base["Revenue"].sum()))
    if "Part_Ingresos_%" in t.columns:
        ok_p = abs(t["Part_Ingresos_%"].sum() - 100) < 0.5 and abs(t["Part_Unidades_%"].sum() - 100) < 0.5
    else:
        ok_p = True
    filas.append({"tabla": nombre, "unidades_ok": ok_u, "ingresos_ok": ok_i, "porcentajes_ok": ok_p})

verificacion = pd.DataFrame(filas)
print(verificacion)
assert verificacion[["unidades_ok", "ingresos_ok", "porcentajes_ok"]].all().all(), "Hay totales que no cuadran"
print("Todos los totales y porcentajes son consistentes con el DataFrame.")

# Dataset preparado y tablas de resultados (rutas relativas al proyecto)
df.to_csv(DIR_DATOS / "dataset_preparado.csv", index=False, encoding="utf-8")
for nombre, (t, _) in tablas.items():
    t.to_csv(DIR_RESULTADOS / f"{nombre}.csv", index=False, encoding="utf-8")
tabla_cambios.to_csv(DIR_RESULTADOS / "registro_transformaciones.csv", index=False, encoding="utf-8")
diccionario_nuevas.to_csv(DIR_RESULTADOS / "variables_incorporadas.csv", index=False, encoding="utf-8")


def generar_resumen(dataframe, ruta):
    b = io.StringIO()
    b.write("RESUMEN DEL DATAFRAME TRANSFORMADO Y ENRIQUECIDO\n")
    b.write("=" * 50 + "\n")
    b.write(f"Dataset: {DATASET_ID}\n")
    b.write(f"Fuente: {FUENTE}\n")
    b.write(f"Fecha de consulta: {FECHA_CONSULTA}\n")
    b.write("Split/configuración: archivo data.csv completo (sin muestreo)\n\n")
    b.write(f"Filas: {dataframe.shape[0]}\n")
    b.write(f"Columnas: {dataframe.shape[1]}\n\n")
    b.write("Columnas, tipos y valores nulos:\n")
    info = pd.DataFrame({"tipo": dataframe.dtypes.astype(str), "nulos": dataframe.isna().sum()})
    b.write(info.to_string() + "\n\n")
    b.write("Estadísticas descriptivas (variables numéricas):\n")
    b.write(dataframe.select_dtypes(include="number").describe().T.round(2).to_string() + "\n\n")
    b.write("Frecuencias de variables categóricas:\n")
    for col in ["ProductCategory", "OutletName", "Location", "CustomerAgeGroup", "CustomerIncomeLevel", "NivelVenta"]:
        b.write(f"\n{col}\n")
        b.write(dataframe[col].value_counts(dropna=False).to_string() + "\n")
    ruta.write_text(b.getvalue(), encoding="utf-8")


RUTA_RESUMEN = DIR_RESULTADOS / "resumen_dataframe_transformado.txt"
generar_resumen(df, RUTA_RESUMEN)

# Comprobación: el archivo coincide con el DataFrame de esta ejecución
texto_resumen = RUTA_RESUMEN.read_text(encoding="utf-8")
assert f"Filas: {df.shape[0]}" in texto_resumen and f"Columnas: {df.shape[1]}" in texto_resumen
assert pd.read_csv(DIR_DATOS / "dataset_preparado.csv").shape == df.shape
print(texto_resumen[:900])

def moneda(x):
    return f"{x:,.0f}".replace(",", ".")


def pct(x):
    return f"{x:.1f}".replace(".", ",") + " %"


def lider(t, columna):
    return t.sort_values(columna, ascending=False).iloc[0]


hallazgos = {}

# P1
ti, tu = lider(p1_categorias, "Ingresos"), lider(p1_categorias, "Unidades")
txt = (f"La categoría con mayores ingresos es {ti['ProductCategory']} ({moneda(ti['Ingresos'])}; "
       f"{pct(ti['Part_Ingresos_%'])} del total). La categoría con más unidades vendidas es "
       f"{tu['ProductCategory']} ({moneda(tu['Unidades'])} unidades; {pct(tu['Part_Unidades_%'])} del total). ")
if ti["ProductCategory"] != tu["ProductCategory"]:
    txt += "Las dos categorías no coinciden, lo que sugiere diferencias en el precio medio por unidad. "
else:
    txt += "Es la misma categoría con ambos criterios. "
txt += "Sin datos de costos no puede afirmarse cuál categoría es más rentable."
hallazgos["P1"] = txt

# P2
tt, tl = lider(p2_tiendas, "Ingresos"), lider(p2_ubicaciones, "Ingresos")
hallazgos["P2"] = (f"La tienda con más ingresos es {tt['OutletName']} ({moneda(tt['Ingresos'])}; {pct(tt['Part_Ingresos_%'])} del total) "
                   f"y la ubicación con más ingresos es {tl['Location']} ({moneda(tl['Ingresos'])}; {pct(tl['Part_Ingresos_%'])} del total). "
                   f"Se analizaron {len(p2_tiendas)} tiendas y {len(p2_ubicaciones)} ubicaciones. "
                   "Una misma ubicación puede agrupar varias tiendas, por lo que ambos niveles no son equivalentes.")

# P3
pico = lider(p3_mensual, "Ingresos")
parciales = p3_mensual[p3_mensual["DiasConVentas"] < 25]["Mes"].tolist()
txt = (f"El periodo analizado abarca {len(p3_mensual)} mes(es). El mes con más ingresos fue {pico['Mes']} "
       f"({moneda(pico['Ingresos'])}).")
if parciales:
    txt += (f" Los meses {', '.join(parciales)} tienen menos de 25 días con ventas registradas; "
            "por eso se incluye el ingreso medio por día, que permite compararlos de forma más justa.")
txt += " Con un periodo tan corto no puede hablarse de estacionalidad."
hallazgos["P3"] = txt

# P4
te, ni = lider(p4_edad, "Ingresos"), lider(p4_ingreso, "Ingresos")
hallazgos["P4"] = (f"El grupo de edad con más ingresos es {te['CustomerAgeGroup']} ({pct(te['Part_Ingresos_%'])} del total) y el nivel de "
                   f"ingreso de cliente con más ventas es {ni['CustomerIncomeLevel']} ({pct(ni['Part_Ingresos_%'])} del total). "
                   "Los datos muestran dónde se concentran las ventas, no por qué.")

lineas = ["HALLAZGOS DEL ANÁLISIS (generado por el notebook)", "=" * 50, ""]
for k, v in hallazgos.items():
    lineas += [k, v, ""]
(DIR_RESULTADOS / "hallazgos.txt").write_text("\n".join(lineas), encoding="utf-8")
for k, v in hallazgos.items():
    print(k, "->", v, "\n")

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

doc = Document()
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.top_margin = sec.bottom_margin = Cm(2.5)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(11)

indice_tablas = []


def parrafo(texto, negrita=False, cursiva=False, alinear=None):
    p = doc.add_paragraph()
    r = p.add_run(texto)
    r.bold, r.italic = negrita, cursiva
    if alinear:
        p.alignment = alinear
    return p


def vinetas(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def tabla_df(datos, titulo, max_filas=12):
    indice_tablas.append(titulo)
    parrafo(f"Tabla {len(indice_tablas)}. {titulo}", negrita=True)
    datos = datos.head(max_filas)
    t = doc.add_table(rows=1, cols=len(datos.columns))
    t.style = "Table Grid"
    for i, c in enumerate(datos.columns):
        celda = t.rows[0].cells[i]
        celda.text = ""
        celda.paragraphs[0].add_run(str(c)).bold = True
    for _, fila in datos.iterrows():
        cels = t.add_row().cells
        for i, v in enumerate(fila):
            if isinstance(v, float) and not pd.isna(v):
                cels[i].text = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elif pd.isna(v):
                cels[i].text = "—"
            else:
                cels[i].text = str(v)
    for fila in t.rows:
        for c in fila.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
    doc.add_paragraph()


# ---------------- Portada ----------------
for _ in range(4):
    doc.add_paragraph()
parrafo("Proyecto integrador – AE3", negrita=True, alinear=WD_ALIGN_PARAGRAPH.CENTER).runs[0].font.size = Pt(16)
parrafo("Transformación y enriquecimiento de datos de ventas minoristas (Retail Sales Performance)",
        negrita=True, alinear=WD_ALIGN_PARAGRAPH.CENTER).runs[0].font.size = Pt(22)
doc.add_paragraph()
for etiqueta in ["Integrantes", "Grupo", "Asignatura: Analítica de Datos", "Docente", "Institución"]:
    valor = "" if ":" in etiqueta else ": [COMPLETAR]"
    parrafo(etiqueta + valor, alinear=WD_ALIGN_PARAGRAPH.CENTER)
parrafo(f"Fecha: {FECHA_CONSULTA}", alinear=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_page_break()

# ---------------- Tabla de contenido ----------------
doc.add_heading("Tabla de contenido", level=1)
p = doc.add_paragraph()
fld = OxmlElement("w:fldSimple")
fld.set(qn("w:instr"), 'TOC \\o "1-2" \\h \\z \\u')
run_xml = OxmlElement("w:r")
txt_xml = OxmlElement("w:t")
txt_xml.text = "Haz clic derecho aquí y elige «Actualizar campo» para generar el índice."
run_xml.append(txt_xml)
fld.append(run_xml)
p._p.append(fld)
doc.add_page_break()

# ---------------- 1. Introducción ----------------
doc.add_heading("1. Introducción", level=1)
parrafo(f"Este documento recoge el avance de la AE3 del proyecto integrador. Se trabaja con el dataset "
        f"{DATASET_ID} de Hugging Face, un conjunto de datos tabular y sintético de ventas minoristas con "
        f"{estado_inicial['filas']} registros y {estado_inicial['columnas']} columnas (consultado el {FECHA_CONSULTA}). "
        "El propósito es transformar y enriquecer los datos para responder, de forma descriptiva, preguntas de negocio "
        "y dejar los resultados organizados para su presentación gráfica en la AE4.")

# ---------------- 2. Necesidad ----------------
doc.add_heading("2. Planteamiento de la necesidad", level=1)
parrafo("Escenario hipotético. La gerencia comercial de una cadena minorista necesita conocer dónde se concentran las ventas "
        "(categorías, tiendas, periodos y segmentos de clientes) para orientar decisiones comerciales. La necesidad es de "
        "información descriptiva; no se trata de un problema observado y comprobado.")
doc.add_heading("Pregunta de análisis y preguntas de negocio", level=2)
vinetas([
    "P1. ¿Qué categorías de producto aportan más unidades e ingresos?",
    "P2. ¿Qué tiendas y ubicaciones generan más ingresos?",
    "P3. ¿Cómo evolucionan las unidades y los ingresos por mes?",
    "P4. ¿Qué segmentos de clientes (edad e ingreso) concentran más ventas?",
])

# ---------------- 3. Justificación y objetivos ----------------
doc.add_heading("3. Justificación y objetivos", level=1)
parrafo("El dataset contiene unidades, ingresos, fecha, tienda, ubicación, categoría y características del cliente, "
        "variables suficientes para describir y comparar las ventas por producto, lugar, tiempo y segmento.")
parrafo("Objetivo general: transformar y enriquecer el dataset para responder descriptivamente las preguntas de negocio planteadas.",
        negrita=True)
vinetas([
    "Revisar y corregir tipos de datos, duplicados y valores faltantes, documentando cada decisión.",
    "Incorporar variables derivadas (mes, trimestre, precio unitario, nivel de venta) a partir de los datos existentes.",
    "Construir una tabla de resultados por cada pregunta y exportarlas para su visualización en la AE4.",
])

# ---------------- 4. Marco teórico ----------------
doc.add_heading("4. Marco teórico inicial", level=1)
parrafo("La analítica descriptiva resume lo ocurrido en los datos mediante agrupaciones, totales, participaciones y comparaciones. "
        "Antes de describir es necesario preparar los datos: corregir tipos, tratar faltantes y duplicados (limpieza o transformación) "
        "y construir variables derivadas que aporten al análisis (enriquecimiento). En este proyecto se usa la librería pandas de Python "
        "para estas operaciones.")

# ---------------- 5. Metodología ----------------
doc.add_heading("5. Metodología", level=1)
doc.add_heading("5.1 Selección y reconocimiento del dataset", level=2)
parrafo(f"Se usó el archivo data.csv completo (sin muestreo) del repositorio {DATASET_ID}, publicado con licencia MIT y marcado como "
        "sintético. Cada fila representa un registro de ventas de una tienda en una fecha y categoría de producto, con información del "
        "perfil de cliente. Alcance: los datos no incluyen costos ni descripciones de campaña, por lo que no se evalúa rentabilidad.")
doc.add_heading("5.2 Transformaciones, reglas de calidad y enriquecimiento", level=2)
parrafo("Cada transformación se aplicó mediante código y se registró con su motivo y los registros afectados:")
tabla_df(tabla_cambios.rename(columns={"paso": "Paso", "detalle": "Detalle", "motivo": "Motivo",
                                        "registros_afectados": "Registros afectados"}),
         "Registro de transformaciones y controles de calidad")
tabla_df(comparacion.reset_index().rename(columns={"index": "Indicador", "antes": "Antes", "despues": "Después"}),
         "Comparación del DataFrame antes y después de la preparación")
parrafo("Enriquecimiento: se calcularon variables derivadas únicamente con los datos existentes (sin unir otras tablas), "
        "por lo que no hubo riesgo de multiplicar registros o importes.")
doc.add_heading("5.3 Procedimiento para responder cada pregunta", level=2)
parrafo("Para cada pregunta se agruparon los datos por la dimensión correspondiente (categoría, tienda, ubicación, mes, edad e ingreso del cliente) "
        "y se calcularon registros, unidades, ingresos, participación porcentual y precio medio por unidad. Se verificó que los totales de cada tabla "
        "coincidieran con los del DataFrame y que las participaciones sumaran 100 %.")

# ---------------- 6. Diccionario ----------------
doc.add_heading("6. Diccionario de variables actualizado", level=1)
parrafo("Los significados de las variables originales se infieren de su nombre y de los valores observados; los que no están "
        "documentados se marcan como pendientes de verificar.")
dic_original = pd.DataFrame([
    ["idx", "Identificador numérico del registro", "Entero", "N/A"],
    ["Date", "Fecha de la venta", "Texto → fecha", "Fecha (AAAA-MM-DD)"],
    ["OutletName", "Nombre de la tienda o punto de venta", "Texto", "N/A"],
    ["Location", "Ubicación de la tienda (pendiente de verificar su nivel geográfico)", "Texto", "N/A"],
    ["ProductCategory", "Categoría del producto vendido", "Texto", "N/A"],
    ["UnitsSold", "Unidades vendidas en el registro", "Entero", "Unidades"],
    ["Revenue", "Ingresos del registro", "Entero", "Moneda no documentada (pendiente de verificar)"],
    ["CustomerAgeGroup", "Rango de edad del cliente", "Texto", "Años (rango)"],
    ["CustomerIncomeLevel", "Nivel de ingreso del cliente (Low, Medium, High)", "Texto", "Categoría"],
    ["Label", "Etiqueta categórica sin definición confirmada (pendiente de verificar); no se usa en el análisis", "Texto", "Categoría"],
], columns=["Variable", "Significado", "Tipo", "Unidad"])
tabla_df(dic_original, "Variables originales del dataset")
tabla_df(diccionario_nuevas.rename(columns={"variable": "Variable", "formula_o_regla": "Fórmula o regla",
                                             "significado": "Significado", "utilidad": "Utilidad"}),
         "Variables incorporadas en el enriquecimiento")

# ---------------- 7. Resultados ----------------
doc.add_heading("7. Resultados y discusión", level=1)
parrafo("Cada pregunta se responde con una tabla y su interpretación. Las tablas completas están en la carpeta resultados/ del repositorio.")
LIMITE = "Limitación: los datos son sintéticos y no incluyen costos; los resultados describen el dataset, no un negocio real."

doc.add_heading("P1. Categorías de producto", level=2)
tabla_df(p1_categorias, "Unidades, ingresos y participación por categoría de producto")
parrafo(hallazgos["P1"])

doc.add_heading("P2. Tiendas y ubicaciones", level=2)
tabla_df(p2_tiendas, "Unidades e ingresos por tienda (primeras filas)")
tabla_df(p2_ubicaciones, "Unidades e ingresos por ubicación")
parrafo(hallazgos["P2"])

doc.add_heading("P3. Evolución mensual", level=2)
tabla_df(p3_mensual, "Unidades e ingresos por mes")
parrafo(hallazgos["P3"])

doc.add_heading("P4. Segmentos de clientes", level=2)
tabla_df(p4_edad, "Unidades e ingresos por grupo de edad")
tabla_df(p4_ingreso, "Unidades e ingresos por nivel de ingreso del cliente")
parrafo(hallazgos["P4"])
parrafo(LIMITE, cursiva=True)

# ---------------- 8. Conclusiones ----------------
doc.add_heading("8. Conclusiones del avance", level=1)
parrafo("Qué permite conocer el análisis:", negrita=True)
vinetas([
    "Qué categorías, tiendas, ubicaciones y segmentos de clientes concentran más unidades e ingresos (P1, P2 y P4).",
    "Cómo se distribuyen las ventas en el tiempo dentro del periodo disponible (P3).",
    "Que los datos preparados y las tablas de resultados quedaron listos para visualizarse en la AE4.",
])
parrafo("Aspectos sin resolver:", negrita=True)
vinetas([
    "No es posible afirmar qué producto o tienda es más rentable: el dataset no contiene costos.",
    "El periodo es corto y no permite concluir estacionalidad; algunos meses pueden estar incompletos.",
    "Los datos son sintéticos: las conclusiones aplican al dataset, no a un negocio real.",
    "El significado de la variable Label y la moneda de Revenue están pendientes de verificar en la ficha del dataset.",
])

# ---------------- 9. Referencias e índices ----------------
doc.add_heading("9. Referencias e índices", level=1)
doc.add_heading("Referencias", level=2)
vinetas([
    f"Hugging Face. {DATASET_ID} [Conjunto de datos]. https://huggingface.co/datasets/{DATASET_ID}. Consultado el {FECHA_CONSULTA}.",
    "Hugging Face. Documentación de Datasets. https://huggingface.co/docs/datasets",
    "The pandas development team. Documentación de pandas. https://pandas.pydata.org/docs/",
    "python-docx. Documentación. https://python-docx.readthedocs.io/",
])
doc.add_heading("Índice de tablas", level=2)
for i, titulo in enumerate(indice_tablas, start=1):
    doc.add_paragraph(f"Tabla {i}. {titulo}")

RUTA_DOCX = DIR_DOCUMENTO / "AE3_documento.docx"
doc.save(RUTA_DOCX)
print("Documento guardado en:", RUTA_DOCX)

# Lista final de archivos generados (rutas relativas al proyecto)
for ruta in sorted(RAIZ.rglob("*")):
    if ruta.is_file() and ruta.suffix in {".csv", ".txt", ".docx"}:
        print(ruta.relative_to(RAIZ))

# En Google Colab: empaquetar y descargar la carpeta con los resultados
try:
    from google.colab import files
    import shutil
    shutil.make_archive("AE3_resultados", "zip", root_dir=RAIZ.parent, base_dir=RAIZ.name)
    files.download("AE3_resultados.zip")
except ImportError:
    print("(Fuera de Colab: no se genera el .zip)")
