# langchain-learning

Guía rápida para ejecutar los scripts de LangChain usando el gestor de entornos **uv**.

## Requisitos previos
- Python 3.11 o superior.
- uv instalado. Si aún no lo tienes, sigue las instrucciones oficiales: <https://docs.astral.sh/uv/getting-started/installation/>.
- Variables de entorno definidas en un archivo `.env` en la raíz del proyecto:
  - `OPENAI_API_KEY` (obligatorio).
  - Opcionales: `MODEL_NAME`, `MODEL_TEMPERATURE`, `DATA_FILE`, `QUESTION_COLUMN`, `ANSWER_COLUMN`, `MODEL_COLUMN`, `DATA_HEADER`.

Instala las dependencias del proyecto con:

```bash
uv sync
```

## Scripts disponibles

Cada script puede ejecutarse directamente con `uv run`. Todos comparten la misma configuración cargada desde `scripts/configs/config.py`.

### `scripts/langchain_simple.py`
- **Qué hace:** Para cada fila del archivo Excel configurado (por defecto `content/preguntas_respuestas.xlsx`), toma la columna de preguntas (`PREGUNTA`) y genera una respuesta breve y precisa con el modelo configurado. Las respuestas se guardan en la columna `MODELO`.
- **Comando:**
  ```bash
  uv run python -m scripts/langchain_simple.py
  ```
- **Salida:** Actualiza el archivo de entrada sobrescribiendo/creando la columna `MODELO` y muestra el DataFrame resultante por consola.

### `scripts/langchain_friendly.py`
- **Qué hace:** Similar al anterior, pero induce al modelo a responder de forma cercana y positiva. Lee la columna definida en `QUESTION_COLUMN` (por defecto `PREGUNTA`) y escribe las respuestas en la columna `MODELO_FRIENDLY`.
- **Comando:**
  ```bash
  uv run python -m scripts/langchain_friendly.py
  ```
- **Salida:** Añade/actualiza la columna `MODELO_FRIENDLY` en el mismo archivo Excel y muestra el DataFrame actualizado.

### `scripts/langchain_async.py`
- **Qué hace:** Analiza opiniones de usuarios (por defecto en `content/opiniones_usuarios.xlsx`, columna F), pide al modelo que devuelva un JSON con `score` (1-10) y `sentiment` (`Positivo`, `Neutro` o `Negativo`) y guarda los resultados.
- **Comando:**
  ```bash
  uv run python -m  scripts/langchain_async.py
  ```
- **Salida:** Genera el archivo `content/opiniones_usuarios_clasificadas.xlsx` con las columnas `puntaje` y `sentimiento` completadas y muestra el DataFrame final.

> **Nota:** Si tus archivos tienen encabezados distintos o están en otra ubicación, ajusta las variables de entorno correspondientes (por ejemplo `DATA_FILE`, `QUESTION_COLUMN` o `DATA_HEADER`). Para modificar la concurrencia del script asíncrono, cambia el valor de `CONCURRENCY_LIMIT` definido al inicio de `scripts/langchain_async.py`.
