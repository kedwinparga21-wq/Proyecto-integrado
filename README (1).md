# Proyecto integrador – Analítica de Datos (IU Digital de Antioquia)

Repositorio del proyecto integrador. Trabaja con un único dataset a lo largo de las actividades.

## Dataset
- **Nombre:** `infinite-dataset-hub/RetailSalesPerformance` (Hugging Face)
- **Enlace:** https://huggingface.co/datasets/infinite-dataset-hub/RetailSalesPerformance
- **Tipo:** tabular (CSV), **sintético** (generado con IA según su ficha), licencia MIT, 100 filas y 10 columnas.
- **Split usado:** `train` (archivo completo, sin muestreo).

## Necesidad (escenario hipotético)
La gerencia comercial de una cadena minorista necesita saber dónde se concentran las ventas (categorías, tiendas, periodos y segmentos de clientes) para orientar sus decisiones.

## Actividades y archivos

| Actividad | Qué contiene | Archivos |
|---|---|---|
| **EA1** – Carga y creación de dataset | Clase que carga datos de Hugging Face, clase que resume un DataFrame en `.txt` y notebook con 6 transformaciones | `hf_dataset_loader.py`, `dataset_summarizer.py`, `EA1_carga_creacion_dataset.ipynb`, `EA1_resumen_dataframe_transformado.txt` |
| **EA2** – Ideación, diseño y documentación | Notebook de descripción básica, resumen `.txt` y documento Word con la necesidad y el diseño | `EA2_exploracion_dataset.ipynb`, `EA2_resumen_dataframe.txt`, `EA2_documento_inicial.docx` |
| **AE3** – Transformación y enriquecimiento | Pipeline, tablas de resultados y documento | `ae3_pipeline.py`, `AE3_transformacion_enriquecimiento.ipynb.txt`, `p1_*.csv` … `p4_*.csv`, `dataset_preparado.csv`, `hallazgos.txt`, `AE3_documento_word.docx` |
| **AE4** – Métricas y visualización | En construcción: aplicación en Streamlit y documento completo en PDF | (se agregará) |

## Clases de Python (EA1)
- `HFDatasetLoader(dataset_id, split="train")` → método `load()` devuelve un DataFrame de pandas.
- `DatasetSummarizer(dataframe, titulo, origen, notas)` → método `guardar(ruta)` genera el resumen en un `.txt` (filas, columnas, tipos, nulos, estadísticas y valores frecuentes).

## Pasos de ejecución
1. Abrir el notebook (`EA1_carga_creacion_dataset.ipynb` o `EA2_exploracion_dataset.ipynb`) en Google Colab o Jupyter.
2. Ejecutar todas las celdas en orden. Se necesita conexión a internet para leer el dataset desde Hugging Face.
3. Si los archivos `.py` no están en la misma carpeta, el notebook los descarga de este repositorio.
4. Cada ejecución **regenera** el archivo `.txt` con rutas relativas (`EA1/resultados/` y `AE2/resultados/`).

Alternativa local: `pip install -r requirements.txt` y abrir el notebook con Jupyter.

## Limitaciones
- No hay costos: no se puede afirmar qué es más rentable.
- Datos sintéticos y periodo corto (1 de enero a 23 de febrero de 2023).
- La moneda de `Revenue` no está especificada en la ficha del dataset.

## Acceso del docente
El repositorio es público.
