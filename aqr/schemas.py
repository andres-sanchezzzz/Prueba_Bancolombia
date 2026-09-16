"""Contratos públicos de los tres módulos; causalidad no implica causa raíz."""
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Tipologia(str, Enum):
    HIPOTECARIA = "Aclaraciones Cartera Hipotecaria"
    RETIRO = "Retiros por Pin Pad Cuenta Corriente"
    GMF = "Gravamen a Movimiento AFC"
    EXTRACTO = "Requerimiento de Extractos Libranza"
    DUPLICADO = "Doblemente Radicado"
    SIN_INFORMACION = "No tramitado por falta de información"


class Cita(StrictModel):
    fuente_id: str = Field(description="Identificador exacto de una fuente suministrada")
    texto: str = Field(description="Fragmento literal, no vacío, de esa fuente")
    uso: Literal["contenido", "ausencia"] = Field(default="contenido",
        description="ausencia solo acredita que ese campo está vacío/NULL, nunca un hecho positivo")


class Clasificacion(StrictModel):
    tipologia: Tipologia
    causalidad: str = Field(description="Motivo específico en lenguaje natural; no catálogo inventado")
    solicitud_principal: str
    solicitudes_secundarias: list[str]
    evidencia: list[Cita]
    justificacion: str = Field(description="Explicación breve de la asignación, sin razonamiento interno")
    asignacion_forzada: bool
    requiere_revision: bool
    razones_revision: list[str]


class Hallazgo(StrictModel):
    id: str = Field(description="Identificador único H1, H2, etc.")
    tipo: Literal["declaracion_cliente", "actuacion_documentada", "dato_registrado", "causa_documentada"]
    descripcion: str
    evidencia: list[Cita]


class Investigacion(StrictModel):
    hallazgos: list[Hallazgo]
    causa_documentada_ids: list[str] = Field(description="IDs de causas documentadas; vacío si no determinada")
    datos_pendientes: list[str]
    limitaciones: list[str]
    requiere_revision: bool
    razones_revision: list[str]


class Parrafo(StrictModel):
    texto: str
    tipo: Literal["hecho", "pendiente", "cortesia"]
    evidencia_ids: list[str] = Field(description="IDs de hallazgos que respaldan el párrafo")
    pendiente_indices: list[int] = Field(description="Índices desde 0 de datos_pendientes usados")


class Respuesta(StrictModel):
    parrafos: list[Parrafo]
    requiere_revision: bool
    razones_revision: list[str]


MODELS = {"clasificacion": Clasificacion, "investigacion": Investigacion, "respuesta": Respuesta}


def response_schema(stage):
    """El proveedor exige todas las propiedades, incluso defaults de compatibilidad."""
    schema = MODELS[stage].model_json_schema()

    def visit(node):
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["required"] = list(node.get("properties", {}))
                node["additionalProperties"] = False
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)
    visit(schema)
    return schema
