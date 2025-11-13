import os
import json
from tavily import TavilyClient
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()
tavily_api_key = os.getenv('TAVILY_API_KEY')
tavily = TavilyClient(api_key=tavily_api_key)

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