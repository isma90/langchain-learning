# langchain-learning

Guía rápida para ejecutar los scripts de LangChain usando el gestor de entornos **uv**.

## Requisitos previos
- Python 3.11 o superior.
- uv instalado. Si aún no lo tienes, sigue las instrucciones oficiales: <https://docs.astral.sh/uv/getting-started/installation/>.
- Variables de entorno definidas en un archivo `.env` en la raíz del proyecto:
  - `OPENAI_API_KEY` (obligatorio).
  - Opcionales: `MODEL_NAME`, `MODEL_TEMPERATURE`, `DATA_FILE`, `QUESTION_COLUMN`, `ANSWER_COLUMN`, `MODEL_COLUMN`, `DATA_HEADER`.
  - Instrumentación opcional con Langfuse: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, `LANGFUSE_ENVIRONMENT`, `LANGFUSE_RELEASE`, `LANGFUSE_TAGS`, `LANGFUSE_METADATA`, `LANGFUSE_ENABLED`.

Instala las dependencias del proyecto con:

```bash
uv sync
```

## Scripts disponibles

Cada script puede ejecutarse directamente con `uv run`. Todos comparten la misma configuración cargada desde `scripts/configs/config.py`.

### `scripts/langchain/simple.py`
- **Qué hace:** Para cada fila del archivo Excel configurado (por defecto `content/preguntas_respuestas.xlsx`), toma la columna de preguntas (`PREGUNTA`) y genera una respuesta breve y precisa con el modelo configurado. Las respuestas se guardan en la columna `MODELO`.
- **Comando:**
  ```bash
  uv run scripts/langchain/simple.py
  ```
- **Salida:** Actualiza el archivo de entrada sobrescribiendo/creando la columna `MODELO` y muestra el DataFrame resultante por consola.

### `scripts/langchain/friendly.py`
- **Qué hace:** Similar al anterior, pero induce al modelo a responder de forma cercana y positiva. Lee la columna definida en `QUESTION_COLUMN` (por defecto `PREGUNTA`) y escribe las respuestas en la columna `MODELO_FRIENDLY`.
- **Comando:**
  ```bash
  uv run scripts/langchain/friendly.py
  ```
- **Salida:** Añade/actualiza la columna `MODELO_FRIENDLY` en el mismo archivo Excel y muestra el DataFrame actualizado.

### `scripts/langchain/async.py`
- **Qué hace:** Analiza opiniones de usuarios (por defecto en `content/opiniones_usuarios.xlsx`, columna F); pide al modelo que devuelva un JSON con `score` (1-10) y `sentiment` (`Positivo`, `Neutro` o `Negativo`) y guarda los resultados.
- **Comando:**
  ```bash
  uv run scripts/langchain/async.py
  ```
- **Salida:** Genera el archivo `content/opiniones_usuarios_clasificadas.xlsx` con las columnas `puntaje` y `sentimiento` completadas y muestra el DataFrame final.

### `scripts/langchain/chat.py`
- **Qué hace:** Demuestra un flujo de conversación con historial persistido en memoria e instrumentación opcional con Langfuse.
- **Comando:**
  ```bash
  uv run scripts/langchain/chat.py
  ```
- **Requisitos:** Debes tener `OPENAI_API_KEY` configurado; si Langfuse no está activo, el script continúa sin enviar trazas.

### `scripts/langchain/chat_redis.py`
- **Qué hace:** Guarda historiales de conversación en Redis (diferentes sesiones) y consulta el modelo reutilizando mensajes anteriores.
- **Comando:**
  ```bash
  uv run scripts/langchain/chat_redis.py
  ```
- **Requisitos:** Además de `OPENAI_API_KEY`, debes definir `REDIS_URL` apuntando a una instancia accesible de Redis (por ejemplo `redis://localhost:6379/0`). El script usa `langchain_community.RedisChatMessageHistory` para la persistencia.

> **Nota:** Si tus archivos tienen encabezados distintos o están en otra ubicación, ajusta las variables de entorno correspondientes (por ejemplo `DATA_FILE`, `QUESTION_COLUMN` o `DATA_HEADER`). Para modificar la concurrencia del script asíncrono, cambia el valor de `CONCURRENCY_LIMIT` definido al inicio de `scripts/langchain/async.py`.

## Instrumentación con Langfuse
- Configura tus credenciales en el archivo `.env` (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` y opcionalmente `LANGFUSE_HOST`). Si necesitas desactivarlo sin borrar las claves, define `LANGFUSE_ENABLED=false`.
- El módulo `scripts/configs/langfuse.py` expone funciones auxiliares:
  - `get_langfuse_settings()` lee y cachea la configuración.
- `build_langfuse_client()` crea un cliente de Langfuse listo para componerse con otras herramientas.
- `build_langfuse_callback()` devuelve un `CallbackHandler` para instrumentar cadenas de LangChain (por ejemplo `chain.invoke(..., config={"callbacks": [handler]})`).
- Puedes enriquecer los rastros añadiendo `LANGFUSE_TAGS` (lista separada por comas) y `LANGFUSE_METADATA` (objeto JSON). Ambos se fusionan con los valores pasados al construir el callback.

## Compatibilidad con APIs antiguas de LangChain
- Las versiones recientes de LangChain ya no exponen el módulo `langchain.memory`. El proyecto incluye `scripts/utils/langchain_shims.py` y `sitecustomize.py` para registrar un módulo compatible y mantener soporte para `from langchain.memory import ChatMessageHistory`, como en notebooks antiguos (por ejemplo en Google Colab).
- Si necesitas usar la API moderna, importa directamente desde `langchain_core.chat_history`. El shim sólo afecta a las rutas clásicas para evitar romper ejercicios existentes.
