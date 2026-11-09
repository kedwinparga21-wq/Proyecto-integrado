# AE3 – Proyecto integrador: Transformación y Enriquecimiento de Datos

Continuación del proyecto integrador (AE2). Se transforma y enriquece un dataset de ventas minoristas para responder, de forma descriptiva, preguntas de negocio y dejar los resultados listos para su visualización en la AE4.

## Dataset
- **Nombre:** `infinite-dataset-hub/RetailSalesPerformance` (Hugging Face)
- **Enlace:** https://huggingface.co/datasets/infinite-dataset-hub/RetailSalesPerformance
- **Tipo:** tabular, **sintético**, licencia MIT
- **Configuración usada:** archivo `data.csv` completo (sin muestreo)
- **Fecha de consulta:** ver `resultados/resumen_dataframe_transformado.txt`

## Necesidad y preguntas de negocio
Escenario hipotético: la gerencia comercial de una cadena minorista necesita saber dónde se concentran las ventas.

| # | Pregunta | Tabla de resultados |
|---|---|---|
| P1 | ¿Qué categorías de producto aportan más unidades e ingresos? | `resultados/p1_categorias.csv` |
| P2 | ¿Qué tiendas y ubicaciones generan más ingresos? | `resultados/p2_tiendas.csv`, `resultados/p2_ubicaciones.csv` |
| P3 | ¿Cómo evolucionan las unidades y los ingresos por mes? | `resultados/p3_mensual.csv` |
| P4 | ¿Qué segmentos de clientes (edad e ingreso) concentran más ventas? | `resultados/p4_edad.csv`, `resultados/p4_ingreso.csv` |

## Transformaciones realizadas
- Conversión de `Date` a fecha y validación numérica de `UnitsSold` y `Revenue`.
- Normalización de espacios en columnas de texto.
- Revisión de duplicados, valores faltantes y valores no positivos (se reportan; no se imputan).
- El detalle de cada paso (qué, por qué y cuántos registros) está en `resultados/registro_transformaciones.csv`.

## Enriquecimiento
Variables calculadas con los datos existentes: `Anio`, `Trimestre`, `Mes`, `DiaSemana`, `FinDeSemana`, `PrecioUnitario` y `NivelVenta`. Fórmulas en `resultados/variables_incorporadas.csv`.

## Estructura del repositorio
```
AE3/
├── README.md
├── requirements.txt
├── notebooks/
│   └── AE3_transformacion_enriquecimiento.ipynb   # notebook ejecutado
├── src/
│   └── ae3_pipeline.py                            # mismo código en formato script
├── datos/
│   ├── dataset_original.csv
│   └── dataset_preparado.csv
├── resultados/
│   ├── p1_categorias.csv ... p4_ingreso.csv       # tablas de resultados
│   ├── registro_transformaciones.csv
│   ├── variables_incorporadas.csv
│   ├── hallazgos.txt
│   └── resumen_dataframe_transformado.txt         # generado por el código
└── documento/
    └── AE3_documento.docx
```

## Pasos de ejecución
1. Abrir `notebooks/AE3_transformacion_enriquecimiento.ipynb` en Google Colab (o Jupyter).
2. Ejecutar todas las celdas (*Entorno de ejecución → Ejecutar todo*). Requiere conexión a internet para leer el dataset desde Hugging Face.
3. El notebook crea las carpetas `datos/`, `resultados/` y `documento/` con rutas relativas y **regenera** el archivo `resultados/resumen_dataframe_transformado.txt` en cada ejecución.

Alternativa por terminal: `pip install -r requirements.txt` y `python src/ae3_pipeline.py`.

## Archivo descriptivo `.txt`
`resultados/resumen_dataframe_transformado.txt` se genera automáticamente desde el DataFrame final e incluye filas, columnas, nombres y tipos, valores nulos y estadísticas descriptivas.

## Limitaciones
- No hay datos de costos: no se puede afirmar qué producto o tienda es más rentable.
- Los datos son sintéticos y el periodo es corto: no se concluye estacionalidad.
- El significado de `Label` y la moneda de `Revenue` están pendientes de verificar en la ficha del dataset.

## Acceso del docente
Si el repositorio es privado, concede acceso de lectura al docente.
