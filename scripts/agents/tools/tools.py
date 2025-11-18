import os
import json
import logging
from langchain.agents.middleware import wrap_tool_call
from tavily import TavilyClient
from langchain.tools import tool
from dotenv import load_dotenv
from textwrap import dedent
from langchain_core.messages import ToolMessage

load_dotenv()
tavily_api_key = os.getenv('TAVILY_API_KEY')
tavily = TavilyClient(api_key=tavily_api_key)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@tool
def buscar(term: str) -> str:
    """Realiza una búsqueda."""
    # Realiza la búsqueda en Tavily
    search = tavily.search(query=term, max_results=5)
    results = search.get("results", [])
    summary = f"Reporte de búsqueda Tavily para el tema '{term}':"
    details = []
    for res in results:
        title = res.get("title", "Sin título")
        url = res.get("url", "")
        content = res.get("content", "")
        details.append(f"- {title}\n  {content}\n  {url}\n")

    return json.dumps({
        "summary": summary,
        "details": "\n".join(details) or "No se encontraron resultados."
    })

@tool
def write_report(report, file_name):
    """Escribe archivos en disco"""
    with open(file_name, "w") as file:
        file.write(report)
    return "File " + file_name + " created Successfully"

@tool
def buscar_politicas(term: str) -> str:
    """Busca una política determinada de la organización, dado un término de búsqueda."""
    # Para fines didácticos, la respuesta está hardcodeada
    term = term.strip()
    return dedent(
        f"""
        [BÚSQUEDA FAKE] Coincidencias para '{term}':
        - Política 2021: describe cómo usar RAG con datos bancarios.
        - Guía 2023: pasos para justificar decisiones ante auditoría.
        - Memo 2024: checklist de privacidad para agentes internos.
        """
    ).strip()


@tool
def auditoria_privacidad(contexto: str) -> str:
    """Herramienta que realiza una auditoría del mensaje para encontrar posibles problemas de privacidad de la información."""
    # Esta herramienta siempre falla, con fines didácticos:
    raise RuntimeError(
        "La auditoría automática encontró campos sin clasificar. Escala a seguridad."
    )


@wrap_tool_call
def manejar_errores_de_tool(request, handler):
    """Devuelve un mensaje de error claro cuando una herramienta truena."""
    from langchain_core.messages import ToolMessage

    try:
        return handler(request)
    except Exception as exc:
        return ToolMessage(
            content=f"⚠️ Auditoría detenida: {exc}",
            tool_call_id=request.tool_call["id"],
        )

@wrap_tool_call
def ToolMonitoringMiddleware(request, handler):
    """
    Middleware que loguea cada invocación de herramienta.
    Captura: nombre, argumentos, éxito/fracaso, tiempo de ejecución.
    """
    import time

    tool_name = request.tool_call.get("name", "unknown")
    tool_args = request.tool_call.get("args", {})
    tool_call_id = request.tool_call.get("id", "unknown")

    start_time = time.time()
    logger.info(f"🔧 [TOOL CALL] {tool_name} | ID: {tool_call_id}")
    logger.info(f"   Argumentos: {json.dumps(tool_args, indent=2, ensure_ascii=False)}")

    try:
        result = handler(request)
        elapsed = time.time() - start_time
        logger.info(f"✅ [SUCCESS] {tool_name} | Tiempo: {elapsed:.2f}s")
        return result
    except Exception as exc:
        elapsed = time.time() - start_time
        logger.error(f"❌ [ERROR] {tool_name} | Error: {exc} | Tiempo: {elapsed:.2f}s")
        return ToolMessage(
            content=f"Error al ejecutar {tool_name}: {str(exc)}",
            tool_call_id=tool_call_id,
        )

@tool
def buscar_informacion_nutricional(ingrediente: str) -> str:
    """
    Busca información nutricional de un ingrediente específico por 100g.
    El LLM debe analizar los resultados y extraer calorías y grasas.
    Retorna los resultados de búsqueda con contexto nutricional.
    """
    query = f"{ingrediente} nutrition facts calories fat per 100g información nutricional calorías grasas"

    try:
        search_result = tavily.search(query=query, max_results=5)
        results = search_result.get("results", [])

        if not results:
            return json.dumps({
                "ingrediente": ingrediente,
                "encontrado": False,
                "mensaje": "No se encontraron resultados de búsqueda"
            }, ensure_ascii=False)

        # Compilar información de búsqueda para que el LLM la procese
        detalles_busqueda = []
        for res in results:
            detalles_busqueda.append(
                f"Título: {res.get('title', '')}\n"
                f"Contenido: {res.get('content', '')}\n"
                f"URL: {res.get('url', '')}"
            )

        respuesta = {
            "ingrediente": ingrediente,
            "encontrado": True,
            "instrucciones": "Extrae de estos resultados: calorías por 100g y gramos de grasas por 100g",
            "resultados_busqueda": "\n---\n".join(detalles_busqueda)
        }

        return json.dumps(respuesta, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error en búsqueda de {ingrediente}: {e}")
        return json.dumps({
            "ingrediente": ingrediente,
            "encontrado": False,
            "error": str(e)
        }, ensure_ascii=False)


@tool
def extraer_datos_nutricionales(información_json: str) -> str:
    """
    Extrae valores de calorías y grasas (en gramos) de la información obtenida.
    Retorna un JSON con calorias y grasas estimadas.
    """
    try:
        info = json.loads(información_json)
        ingrediente = info.get("ingrediente", "desconocido")

        if not info.get("encontrado"):
            return json.dumps({
                "ingrediente": ingrediente,
                "calorias": 0,
                "grasas_gramos": 0,
                "nota": "No se encontraron datos"
            })

        # Compilar información de todas las fuentes
        texto_completo = " ".join([
            f["contenido"] for f in info.get("fuentes", [])
        ])

        # Patrones simples para extraer datos (en producción usarías NER o regex más robustos)
        calorias = _extraer_numero(texto_completo, r"(\d+)\s*(?:kcal|calorías|calories)")
        grasas = _extraer_numero(texto_completo, r"(\d+(?:\.\d+)?)\s*(?:g|gramos)\s*(?:de\s+)?grasas")

        return json.dumps({
            "ingrediente": ingrediente,
            "calorias": calorias,
            "grasas_gramos": grasas,
            "fuente_encontrada": True
        })

    except Exception as e:
        logger.error(f"Error extrayendo datos: {e}")
        return json.dumps({
            "calorias": 0,
            "grasas_gramos": 0,
            "error": str(e)
        })

def _extraer_numero(texto: str, patron: str) -> float:
    """Utilidad para extraer números de un patrón regex"""
    import re
    match = re.search(patron, texto, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return 0.0
    return 0.0

@tool
def escribir_archivo(nombre: str, contenido: str) -> str:
    """Escribe un archivo de texto en disco. ACCIÓN SENSIBLE."""
    with open(nombre, "w", encoding="utf-8") as f:
        f.write(contenido)
    return f"✓ Archivo '{nombre}' creado exitosamente."