API Endpoints
=============

Esta sección documenta los endpoints disponibles en la API, basándose en la especificación OpenAPI.

Actualización del esquema OpenAPI
----------------------------------

Antes de generar la documentación, asegúrate de tener el backend en ejecución:

.. code-block:: bash

    cd backend
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Luego, desde el directorio `docs`, ejecuta:

.. code-block:: bash

    make openapi
    make html

El objetivo `openapi` descarga la especificación JSON en `source/openapi.json`.

Inclusión de la especificación
------------------------------

.. openapi:: openapi.json
   :style: json
   :caption: Especificación OpenAPI de la API