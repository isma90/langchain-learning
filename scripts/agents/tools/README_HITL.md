# Human-in-the-Loop (HITL) Interaction Module

Módulo reutilizable para manejar la interacción con el usuario en flujos de Human-in-the-Loop con LangChain.

## Descripción

El módulo `hitl_interaction.py` proporciona funciones para:

1. **Mostrar acciones pendientes** del agente de forma clara y estructurada
2. **Solicitar decisiones** del usuario (approve, edit, reject)
3. **Procesar cada tipo de decisión** con la lógica correspondiente
4. **Mostrar resultados finales** de forma formateada

## Diagrama de Flujo de Funciones

```mermaid
graph TD
    A["🚀 Agente LLM<br/>Intenta usar herramienta sensible"] -->|Interceptado| B["__interrupt__<br/>HumanInTheLoopMiddleware"]

    B -->|Flujo Principal| C["manejar_hitl_interactivo<br/>Función Orquestadora"]

    C -->|1. Mostrar| D["mostrar_accion_pendiente<br/>Muestra tabla con parámetros"]

    D -->|2. Solicitar| E["solicitar_decision_usuario<br/>Pide approve/edit/reject"]

    E -->|Decisión| F{¿Cuál es<br/>la decisión?}

    F -->|approve| G["procesar_approve<br/>Ejecuta sin cambios"]
    F -->|edit| H["procesar_edit<br/>Permite editar parámetros"]
    F -->|reject| I["procesar_reject<br/>Rechaza con motivo"]

    G -->|Resume| J["Command.resume<br/>Agent.invoke"]
    H -->|Resume| J
    I -->|Resume| J

    J -->|Retorna| K["resultado_final<br/>Dict con respuesta del agente"]

    K -->|Mostrar| L["mostrar_resultado_final<br/>Presenta resultado al usuario"]

    L -->|Fin| M["✅ Proceso completado"]

    style A fill:#4A90E2,color:#fff
    style B fill:#F5A623,color:#fff
    style C fill:#7ED321,color:#fff
    style D fill:#50E3C2,color:#000
    style E fill:#50E3C2,color:#000
    style F fill:#BD10E0,color:#fff
    style G fill:#FF6B6B,color:#fff
    style H fill:#FFD93D,color:#000
    style I fill:#E74C3C,color:#fff
    style J fill:#9B59B6,color:#fff
    style M fill:#27AE60,color:#fff
```

## Diagrama de Funciones y Dependencias

```mermaid
graph LR
    subgraph Principal["🎯 Función Principal"]
        MAIN["manejar_hitl_interactivo<br/>(resultado, agent, thread_id)"]
    end

    subgraph Presentacion["📊 Presentación"]
        MOSTRAR["mostrar_accion_pendiente<br/>(action_requests)"]
        RESULTADO["mostrar_resultado_final<br/>(resultado)"]
    end

    subgraph Usuario["👤 Interacción Usuario"]
        DECISION["solicitar_decision_usuario<br/>() → str"]
    end

    subgraph Procesamiento["⚙️ Procesamiento"]
        APPROVE["procesar_approve<br/>(agent, thread_id)"]
        EDIT["procesar_edit<br/>(agent, thread_id, actions)"]
        REJECT["procesar_reject<br/>(agent, thread_id)"]
    end

    MAIN -->|Detecta| MOSTRAR
    MOSTRAR -->|Luego| DECISION
    DECISION -->|Si approve| APPROVE
    DECISION -->|Si edit| EDIT
    DECISION -->|Si reject| REJECT
    APPROVE -->|Ejecuta| RESULTADO
    EDIT -->|Ejecuta| RESULTADO
    REJECT -->|Ejecuta| RESULTADO

    style MAIN fill:#7ED321,stroke:#333,stroke-width:3px,color:#000
    style MOSTRAR fill:#50E3C2,stroke:#333,stroke-width:2px,color:#000
    style DECISION fill:#50E3C2,stroke:#333,stroke-width:2px,color:#000
    style RESULTADO fill:#50E3C2,stroke:#333,stroke-width:2px,color:#000
    style APPROVE fill:#FF6B6B,stroke:#333,stroke-width:2px,color:#fff
    style EDIT fill:#FFD93D,stroke:#333,stroke-width:2px,color:#000
    style REJECT fill:#E74C3C,stroke:#333,stroke-width:2px,color:#fff
```

## Funciones Disponibles

### `manejar_hitl_interactivo(resultado_inicial, agent, thread_id)`

Función principal que maneja todo el flujo HITL de forma interactiva.

**Parámetros:**
- `resultado_inicial` (Dict): Resultado de la invocación inicial del agente
- `agent`: El agente de LangChain
- `thread_id` (str): ID del thread para la ejecución

**Retorna:**
- Dict: Resultado final después de la decisión del usuario
- None: Si no hay acciones pendientes

**Ejemplo:**
```python
from scripts.agents.tools.hitl_interaction import manejar_hitl_interactivo

resultado = agent.invoke(
    {"messages": [{"role": "user", "content": "..."}]},
    config={"configurable": {"thread_id": "demo-001"}}
)

resultado_final = manejar_hitl_interactivo(
    resultado_inicial=resultado,
    agent=agent,
    thread_id="demo-001"
)
```

### `mostrar_accion_pendiente(action_requests)`

Muestra información estructurada sobre las acciones pendientes en una tabla formateada.

**Parámetros:**
- `action_requests` (list): Lista de acciones pendientes del agente

### `solicitar_decision_usuario()`

Solicita al usuario que elija entre approve, edit o reject.

**Retorna:**
- str: La decisión del usuario

### `procesar_approve(agent, thread_id)`

Procesa la decisión de aprobación.

**Parámetros:**
- `agent`: El agente de LangChain
- `thread_id` (str): ID del thread

**Retorna:**
- Dict: Resultado de la ejecución

### `procesar_edit(agent, thread_id, action_requests)`

Procesa la decisión de edición, permitiendo modificar parámetros.

**Parámetros:**
- `agent`: El agente de LangChain
- `thread_id` (str): ID del thread
- `action_requests` (list): Lista de acciones pendientes

**Retorna:**
- Dict: Resultado de la ejecución

### `procesar_reject(agent, thread_id)`

Procesa la decisión de rechazo.

**Parámetros:**
- `agent`: El agente de LangChain
- `thread_id` (str): ID del thread

**Retorna:**
- Dict: Resultado de la ejecución

### `mostrar_resultado_final(resultado)`

Muestra el resultado final de la ejecución del agente.

**Parámetros:**
- `resultado` (Dict): Resultado del agente

## Ejemplo Completo

Ver `class2-E2.py` para un ejemplo completo de uso.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from scripts.agents.tools.hitl_interaction import (
    manejar_hitl_interactivo,
    mostrar_resultado_final,
)

# Crear agente con HITL middleware
agent = create_agent(
    model=init_chat_model("openai:gpt-4o-mini"),
    tools=[mi_herramienta_sensible],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "mi_herramienta_sensible": {
                    "allowed_decisions": ["approve", "edit", "reject"]
                }
            }
        )
    ],
    checkpointer=InMemorySaver(),
)

# Invocar agente
resultado = agent.invoke(
    {"messages": [{"role": "user", "content": "..."}]},
    config={"configurable": {"thread_id": "demo-001"}}
)

# Manejar interacción HITL
resultado_final = manejar_hitl_interactivo(
    resultado_inicial=resultado,
    agent=agent,
    thread_id="demo-001"
)

# Mostrar resultado
if resultado_final:
    mostrar_resultado_final(resultado_final)
```

## Características

- ✅ Interfaz interactiva clara con colores
- ✅ Tablas formateadas para mostrar acciones
- ✅ Soporte para approve, edit y reject
- ✅ Edición de parámetros con valores por defecto
- ✅ Manejo de errores y validación
- ✅ Completamente reutilizable en otros scripts
- ✅ Funciones granulares para máxima flexibilidad

## Diagrama de Arquitectura Completa

```mermaid
graph TB
    subgraph Agent["🤖 AGENTE LANGCHAIN"]
        LLM["Modelo LLM<br/>gpt-4o-mini"]
        TOOLS["Herramientas<br/>- Sensible<br/>- Normal"]
    end

    subgraph Middleware["🛡️ MIDDLEWARE"]
        HITL_MW["HumanInTheLoopMiddleware<br/>interrupt_on: sensible"]
    end

    subgraph HITL_MODULE["📦 HITL MODULE<br/>hitl_interaction.py"]
        MAIN_FUNC["manejar_hitl_interactivo<br/>ORQUESTADOR PRINCIPAL"]
        DISPLAY["mostrar_accion_pendiente<br/>+ mostrar_resultado_final"]
        INPUT["solicitar_decision_usuario"]
        PROCESS["procesar_approve<br/>procesar_edit<br/>procesar_reject"]
    end

    subgraph User["👤 USUARIO"]
        INTERACTION["Input: approve/edit/reject"]
    end

    subgraph Result["📊 SALIDA"]
        OUTPUT["Resultado Final<br/>con respuesta del agente"]
    end

    LLM -->|Intenta herramienta| TOOLS
    TOOLS -->|Acción sensible| HITL_MW
    HITL_MW -->|__interrupt__| MAIN_FUNC

    MAIN_FUNC -->|1️⃣| DISPLAY
    DISPLAY -->|2️⃣| INPUT
    INPUT -->|Usuario responde| INTERACTION
    INTERACTION -->|3️⃣| PROCESS
    PROCESS -->|Command.resume| LLM
    LLM -->|Ejecuta/Rechaza| OUTPUT

    style LLM fill:#4A90E2,color:#fff,stroke:#333,stroke-width:2px
    style TOOLS fill:#4A90E2,color:#fff,stroke:#333,stroke-width:2px
    style HITL_MW fill:#F5A623,color:#fff,stroke:#333,stroke-width:2px
    style MAIN_FUNC fill:#7ED321,color:#000,stroke:#333,stroke-width:3px
    style DISPLAY fill:#50E3C2,color:#000,stroke:#333,stroke-width:2px
    style INPUT fill:#50E3C2,color:#000,stroke:#333,stroke-width:2px
    style PROCESS fill:#9B59B6,color:#fff,stroke:#333,stroke-width:2px
    style INTERACTION fill:#FF6B6B,color:#fff,stroke:#333,stroke-width:2px
    style OUTPUT fill:#27AE60,color:#fff,stroke:#333,stroke-width:2px
```

## Casos de Uso

### 1. **Aprobación Simple (Approve)**
```
Usuario ve acción → Presiona 'approve' → Se ejecuta tal cual → Resultado final
```

### 2. **Edición de Parámetros (Edit)**
```
Usuario ve acción → Presiona 'edit' → Modifica parámetros → Se ejecuta editada → Resultado final
```

### 3. **Rechazo (Reject)**
```
Usuario ve acción → Presiona 'reject' → Especifica motivo → Se rechaza → Respuesta del agente sobre rechazo
```

## Flujo de Control Detallado

```mermaid
sequenceDiagram
    participant U as Usuario
    participant A as Agente
    participant M as HITL Module
    participant LG as LangGraph

    A->>A: Intenta usar herramienta sensible
    A->>LG: HumanInTheLoopMiddleware
    LG->>LG: Detecta interrupción
    LG->>M: Retorna __interrupt__

    M->>M: manejar_hitl_interactivo()
    M->>U: mostrar_accion_pendiente()
    U->>U: Visualiza tabla de acciones

    M->>U: solicitar_decision_usuario()
    U->>M: Responde: approve/edit/reject

    alt Usuario aprueba
        M->>M: procesar_approve()
        M->>LG: Command.resume(approve)
    else Usuario edita
        M->>U: Pide nuevos valores
        U->>M: Proporciona valores editados
        M->>M: procesar_edit()
        M->>LG: Command.resume(edit)
    else Usuario rechaza
        M->>U: Pide motivo
        U->>M: Proporciona motivo
        M->>M: procesar_reject()
        M->>LG: Command.resume(reject)
    end

    LG->>A: Reanuda ejecución
    A->>A: Ejecuta/Rechaza acción
    LG->>M: Retorna resultado_final

    M->>U: mostrar_resultado_final()
    U->>U: Visualiza resultado
```

## Dependencias

- `langchain`
- `langgraph`
- `rich` (para formateo de salida)
