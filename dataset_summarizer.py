# -*- coding: utf-8 -*-
"""Clase para resumir un DataFrame de pandas en un archivo .txt.

Proyecto integrador - Analítica de Datos (IU Digital de Antioquia).
"""

import datetime as dt
import io
from pathlib import Path

import pandas as pd


class DatasetSummarizer:
    """Recibe un DataFrame y genera un resumen de su contenido en un archivo de texto.

    El resumen incluye: filas y columnas, nombres y tipos, valores nulos por columna,
    estadísticas descriptivas de las variables numéricas y frecuencias de las categóricas.

    Parámetros
    ----------
    dataframe : pandas.DataFrame
        Datos que se van a resumir (por ejemplo, el DataFrame ya transformado).
    titulo : str, opcional
        Título que aparece al inicio del resumen.
    origen : dict, opcional
        Datos de origen (dataset_id, split, url...) para dejarlos documentados.
    notas : list[str], opcional
        Lista de notas, por ejemplo las transformaciones aplicadas.
    max_categorias : int, opcional
        Cantidad máxima de valores que se muestran por columna categórica.
    """

    def __init__(self, dataframe, titulo="Resumen del DataFrame", origen=None, notas=None, max_categorias=5):
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("DatasetSummarizer necesita un DataFrame de pandas.")
        self.dataframe = dataframe
        self.titulo = titulo
        self.origen = origen or {}
        self.notas = notas or []
        self.max_categorias = max_categorias

    def construir_resumen(self):
        """Arma el texto del resumen a partir del DataFrame recibido."""
        df = self.dataframe
        salida = io.StringIO()

        salida.write(self.titulo.upper() + "\n")
        salida.write("=" * max(len(self.titulo), 40) + "\n")
        salida.write(f"Generado: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for clave, valor in self.origen.items():
            salida.write(f"{clave}: {valor}\n")
        salida.write("\n")

        salida.write(f"Filas: {df.shape[0]}\n")
        salida.write(f"Columnas: {df.shape[1]}\n\n")

        salida.write("Columnas, tipos de datos y valores nulos:\n")
        info = pd.DataFrame({"tipo": df.dtypes.astype(str), "nulos": df.isna().sum()})
        salida.write(info.to_string() + "\n")
        salida.write(f"Total de valores nulos: {int(df.isna().sum().sum())}\n\n")

        numericas = df.select_dtypes(include="number")
        if not numericas.empty:
            salida.write("Estadísticas descriptivas (variables numéricas):\n")
            salida.write(numericas.describe().T.round(2).to_string() + "\n\n")

        categoricas = df.select_dtypes(include=["object", "string", "category", "bool"])
        if not categoricas.empty:
            salida.write(f"Valores más frecuentes (variables de texto o categóricas, máximo {self.max_categorias}):\n")
            for columna in categoricas.columns:
                salida.write(f"\n{columna} ({df[columna].nunique()} valores distintos)\n")
                salida.write(df[columna].value_counts(dropna=False).head(self.max_categorias).to_string() + "\n")
            salida.write("\n")

        if self.notas:
            salida.write("Notas:\n")
            for nota in self.notas:
                salida.write(f"- {nota}\n")

        return salida.getvalue()

    def guardar(self, ruta):
        """Guarda el resumen en un .txt (UTF-8). Crea la carpeta si no existe. Devuelve la ruta."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(self.construir_resumen(), encoding="utf-8")
        return ruta
