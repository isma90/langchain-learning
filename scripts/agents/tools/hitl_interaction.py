"""
Módulo para manejar la interacción con el usuario en Human-in-the-Loop (HITL).
Proporciona funciones reutilizables para mostrar acciones pendientes y gestionar
decisiones del usuario (approve, edit, reject).
"""

from typing import Dict, Any, Tuple, Optional
from rich import print as rprint
from rich.table import Table
from rich.panel import Panel
from langgraph.types import Command


def mostrar_accion_pendiente(action_requests: list) -> None:
    """
    Muestra información estructurada sobre las acciones pendientes.

    Args:
        action_requests: Lista de acciones pendientes del agente
    """
    rprint("\n[bold]Acción solicitada por el agente:[/bold]\n")

    for action in action_requests:
        table = Table(title=f"Acción: {action['name']}")
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="green")

        for param_name, param_value in action["args"].items():
            # Truncar valores largos para mejor presentación
            valor_display = (
                str(param_value)[:80] + "..."
                if len(str(param_value)) > 80
                else str(param_value)
            )
            table.add_row(param_name, valor_display)

        rprint(table)
    rprint()


def solicitar_decision_usuario() -> str:
    """
    Solicita al usuario que elija entre approve, edit o reject.

    Returns:
        str: La decisión del usuario (approve, edit, reject)
    """
    rprint("[bold]Opciones disponibles:[/bold]")
    rprint("  [green]approve[/green]  - Ejecutar la acción tal cual")
    rprint("  [yellow]edit[/yellow]     - Modificar argumentos antes de ejecutar")
    rprint("  [red]reject[/red]    - Rechazar la acción\n")

    decision = input("Por favor responda con 'approve', 'edit' o 'reject': ").strip().lower()
    return decision


def procesar_approve(agent, thread_id: str) -> Dict[str, Any]:
    """
    Procesa la decisión de aprobación.

    Args:
        agent: El agente de LangChain
        thread_id: ID del thread para la ejecución

    Returns:
        Dict: Resultado de la ejecución del agente
    """
    rprint(Panel(
        "[bold green]✅ DECISIÓN: APPROVE[/bold green]\n"
        "Ejecutando la acción tal cual fue solicitada...",
        border_style="green"
    ))

    resultado_final = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config={"configurable": {"thread_id": thread_id}},
    )

    rprint("\n[bold green]✓ Acción ejecutada correctamente[/bold green]")
    return resultado_final


def procesar_edit(agent, thread_id: str, action_requests: list) -> Dict[str, Any]:
    """
    Procesa la decisión de edición, permitiendo modificar parámetros.

    Args:
        agent: El agente de LangChain
        thread_id: ID del thread para la ejecución
        action_requests: Lista de acciones pendientes

    Returns:
        Dict: Resultado de la ejecución del agente
    """
    rprint(Panel(
        "[bold yellow]📝 DECISIÓN: EDIT[/bold yellow]\n"
        "Modifica los parámetros de la acción...",
        border_style="yellow"
    ))

    # Recuperar valores actuales
    actual_action = action_requests[0]
    args_actuales = actual_action["args"]

    rprint(f"\n[bold]Valores actuales:[/bold]")
    for param_name, param_value in args_actuales.items():
        valor_display = (
            str(param_value)[:60] + "..."
            if len(str(param_value)) > 60
            else str(param_value)
        )
        rprint(f"  {param_name}: {valor_display}")
    rprint()

    # Solicitar nuevos valores
    rprint("[bold]Ingresa los nuevos valores (deja en blanco para mantener el actual):[/bold]\n")

    args_editados = {}
    for param_name, param_value in args_actuales.items():
        prompt = f"Nuevo {param_name} [{str(param_value)[:30]}...]: "
        nuevo_valor = input(prompt).strip()

        if not nuevo_valor:
            args_editados[param_name] = param_value
        else:
            args_editados[param_name] = nuevo_valor

    rprint(Panel(
        f"[bold]Ejecutando con valores editados...[/bold]\n" +
        "\n".join([f"{k}: {str(v)[:60]}" for k, v in args_editados.items()]),
        border_style="yellow"
    ))

    resultado_final = agent.invoke(
        Command(
            resume={
                "decisions": [
                    {
                        "type": "edit",
                        "edited_action": {
                            "name": actual_action["name"],
                            "args": args_editados,
                        },
                    }
                ]
            }
        ),
        config={"configurable": {"thread_id": thread_id}},
    )

    rprint("\n[bold green]✓ Acción editada y ejecutada[/bold green]")
    return resultado_final


def procesar_reject(agent, thread_id: str) -> Dict[str, Any]:
    """
    Procesa la decisión de rechazo.

    Args:
        agent: El agente de LangChain
        thread_id: ID del thread para la ejecución

    Returns:
        Dict: Resultado de la ejecución del agente
    """
    rprint(Panel(
        "[bold red]❌ DECISIÓN: REJECT[/bold red]\n"
        "¿Cuál es el motivo del rechazo?",
        border_style="red"
    ))

    motivo = input("Motivo: ").strip()
    if not motivo:
        motivo = "Rechazado por el usuario sin especificar motivo"

    resultado_final = agent.invoke(
        Command(
            resume={
                "decisions": [
                    {"type": "reject", "message": motivo}
                ]
            }
        ),
        config={"configurable": {"thread_id": thread_id}},
    )

    rprint(f"\n[bold red]✓ Acción rechazada[/bold red]")
    return resultado_final


def manejar_hitl_interactivo(
    resultado_inicial: Dict[str, Any],
    agent,
    thread_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Función principal que maneja todo el flujo de Human-in-the-Loop de forma interactiva.

    Detecta si hay acciones pendientes (`__interrupt__`), muestra la información
    al usuario y gestiona su decisión (approve, edit, reject).

    Args:
        resultado_inicial: Resultado de la invocación inicial del agente
        agent: El agente de LangChain
        thread_id: ID del thread para la ejecución

    Returns:
        Optional[Dict]: Resultado final después de la decisión del usuario,
                       o None si no hay acciones pendientes
    """
    # Verificar si hay interrupción por acción sensible
    if "__interrupt__" not in resultado_inicial:
        rprint(Panel(
            "[bold green]✓ No se detectaron acciones sensibles[/bold green]\n"
            "El agente no requirió aprobación manual.",
            border_style="green"
        ))
        return None

    # Mostrar que se detectó acción sensible
    rprint(Panel(
        "[bold red]⚠️  ACCIÓN SENSIBLE DETECTADA[/bold red]",
        title="HUMAN-IN-THE-LOOP ACTIVATED",
        border_style="red"
    ))

    # Extraer detalles de la acción pendiente
    interrupt_data = resultado_inicial["__interrupt__"][0]
    action_requests = interrupt_data.value["action_requests"]

    # Mostrar la acción
    mostrar_accion_pendiente(action_requests)

    # Solicitar decisión
    decision = solicitar_decision_usuario()

    # Procesar según la decisión
    if decision == "approve":
        resultado_final = procesar_approve(agent, thread_id)

    elif decision == "edit":
        resultado_final = procesar_edit(agent, thread_id, action_requests)

    elif decision == "reject":
        resultado_final = procesar_reject(agent, thread_id)

    else:
        rprint("[bold red]❌ Opción no reconocida. Rechazando por defecto...[/bold red]")
        resultado_final = agent.invoke(
            Command(
                resume={
                    "decisions": [
                        {"type": "reject", "message": "Opción inválida"}
                    ]
                }
            ),
            config={"configurable": {"thread_id": thread_id}},
        )

    return resultado_final


def mostrar_resultado_final(resultado: Dict[str, Any]) -> None:
    """
    Muestra el resultado final de la ejecución del agente.

    Args:
        resultado: Resultado del agente
    """
    rprint("\n[bold blue]" + "=" * 70 + "[/bold blue]")
    rprint("[bold blue]📋 RESULTADO FINAL[/bold blue]\n")

    if "messages" in resultado and resultado["messages"]:
        last_message = resultado["messages"][-1]
        rprint(f"[bold]Respuesta del agente:[/bold]\n{last_message.content}\n")
    else:
        rprint("[italic]No hay mensajes en el resultado[/italic]\n")
