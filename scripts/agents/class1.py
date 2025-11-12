import os
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from rich import print
from rich.pretty import Pretty

load_dotenv()
MODEL = 'gpt-5-mini'

def running_in_colab() -> bool:
    try:
        import google.colab  # type: ignore
        return True
    except ImportError:
        return False


def get_secret(key: str, *, required: bool = True) -> Optional[str]:
    """Return a secret regardless of the runtime."""
    value = os.getenv(key)
    if value:
        return value
    if running_in_colab():
        from google.colab import userdata  # type: ignore
        value = userdata.get(key)
        if value:
            os.environ[key] = value
    else:
        value = os.getenv(key)
    if required and not value:
        raise RuntimeError(f'Environment variable {key} is not set.')
    return value


def configure_environment(required_keys: Iterable[str]) -> None:
    for key in required_keys:
        get_secret(key)

configure_environment(["OPENAI_API_KEY"])

client = OpenAI()

# por ahora vamos a hardcodar las respuesta, pero en esta función podemos
# hacer una llamada a una API que nos responda con la información correcta
def get_current_weather(location, unit="fahrenheit"):
    """Obtener el clima actual en una ubicación específica"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "15", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

# Paso 1: enviar al modelo la conversación y las funciones que tiene disponibles
messages = [{"role": "user", "content": "Cómo está el clima en San Francisco, Tokyo y Paris?"}]
print("Mensaje inicial:")
print(Pretty(messages))

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Obtener el clima actual en una ubicación específica",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "La ciudad y estado, por ejemplo: San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=tools,
    tool_choice="auto",  # auto es el valor por defecto, también puede ser required (al menos llamar a una), none o function (para llamar a una función particular)
)
response_message = response.choices[0].message
print ("Respuesta  a la primera llamada:")
print(Pretty(response_message))



tool_calls = response_message.tool_calls
# Paso 2: checkear si el modelo pidió ejecutar una función
if tool_calls:
    # Paso 3: llamar a la función
    # Nota: la respuesta JSON podría no siempre ser válida, tenemos que capturar esos errores
    available_functions = {
        "get_current_weather": get_current_weather,
    }  # en este ejemplo hay una sola función, pero podría haber más
    messages.append(response_message)  # agregar la respuesta del asistente al historial de conversación

    # Paso 4: enviar la información de cada function call y respuesta correspondiente
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        print("\nLlamando a función: " + function_name)
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        print ("Argumentos de la función:")
        print(Pretty(function_args))
        function_response = function_to_call(**function_args)
        print("Respuesta de la función:")
        print(Pretty(function_response))
        new_message=(
            {
                "tool_call_id": tool_call.id,
                "role": "tool", # se utiliza para indicarle al modelo que es la respuesta de la función de la herramienta que se ejecutó
                "name": function_name,
                "content": function_response,
            }
        )
        messages.append(new_message)  # agregar la respuesta de la función al historial de conversación
        print("Nuevo mensaje:")
        print(Pretty(new_message))
    # ahora podemos volver a llamar al modelo, que encontrará las respuestas a las llamadas de función en el historial
    second_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    print("\nSegunda respuesta:")
    print(second_response.choices[0].message.content)