# -*- coding: utf-8 -*-
"""Clase para obtener un dataset de Hugging Face y devolverlo como DataFrame de pandas.

Proyecto integrador - Analítica de Datos (IU Digital de Antioquia).
"""

import pandas as pd


class HFDatasetLoader:
    """Conecta con Hugging Face Datasets, carga un dataset y lo entrega como DataFrame.

    Parámetros
    ----------
    dataset_id : str
        Identificador del repositorio, por ejemplo "infinite-dataset-hub/RetailSalesPerformance".
    split : str, opcional
        Partición a cargar (por defecto "train").
    config_name : str, opcional
        Configuración del dataset, cuando el repositorio tiene varias.
    revision : str, opcional
        Versión o revisión específica del repositorio (rama, etiqueta o commit).
    """

    def __init__(self, dataset_id, split="train", config_name=None, revision=None):
        if not isinstance(dataset_id, str) or "/" not in dataset_id:
            raise ValueError(
                "dataset_id debe tener el formato 'usuario/nombre', "
                "por ejemplo 'infinite-dataset-hub/RetailSalesPerformance'."
            )
        self.dataset_id = dataset_id
        self.split = split
        self.config_name = config_name
        self.revision = revision
        self.dataframe = None

    @property
    def url(self):
        """Enlace directo a la ficha del dataset en Hugging Face."""
        return f"https://huggingface.co/datasets/{self.dataset_id}"

    def load(self):
        """Descarga el dataset desde Hugging Face y lo devuelve como DataFrame de pandas."""
        try:
            from datasets import load_dataset
        except ImportError as error:
            raise ImportError(
                "Falta la librería 'datasets'. Instálala con: pip install datasets"
            ) from error

        try:
            dataset = load_dataset(
                self.dataset_id,
                self.config_name,
                split=self.split,
                revision=self.revision,
            )
        except Exception as error:
            raise RuntimeError(
                f"No se pudo cargar '{self.dataset_id}' (split='{self.split}'). "
                f"Revisa el identificador, el split y la conexión a internet. Detalle: {error}"
            ) from error

        self.dataframe = dataset.to_pandas()
        return self.dataframe

    def describe_source(self):
        """Devuelve un diccionario con los datos de origen usados en la carga."""
        return {
            "dataset_id": self.dataset_id,
            "url": self.url,
            "split": self.split,
            "config_name": self.config_name,
            "revision": self.revision,
        }
