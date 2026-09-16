"""LangGraph ordena tres llamadas independientes y validaciones entre etapas."""
import importlib.metadata
import json
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from .prompts import PROMPTS, VERSION
from .budget import BudgetStop
from .provider import StageFailure
from .schemas import MODELS, response_schema
from .storage import atomic_json, digest, read_json
from .validation import review_reasons, validate_stage


class State(TypedDict):
    case: dict
    outputs: dict
    metadata: dict
    errors: list[str]
    status: str
    stop_batch: bool


def workflow_fingerprint(config):
    code = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path(__file__).parent.glob("*.py"))}
    dependencies = {name: importlib.metadata.version(name)
                    for name in ("openai", "langgraph", "pydantic", "openpyxl")}
    return digest({"config": config, "prompt_version": VERSION, "prompts": PROMPTS,
                   "schemas": {k: v.model_json_schema() for k, v in MODELS.items()},
                   "code": code, "dependencies": dependencies})


def stage_payload(stage, case, outputs):
    if stage == "clasificacion":
        return {"fuentes": [s for s in case["sources"] if s["id"].startswith("radicado:")]}
    if stage == "investigacion":
        return {"fuentes": case["sources"], "cruce": case["join"],
                "clasificacion_propuesta": outputs["clasificacion"]}
    return {"clasificacion_propuesta": outputs["clasificacion"],
            "investigacion": outputs["investigacion"], "cruce": case["join"],
            "pendientes_con_indice": [{"indice": i, "texto": text} for i, text in
                                      enumerate(outputs["investigacion"]["datos_pendientes"])]}


def build_graph(provider, stage_dir: Path, fingerprint: str):
    def make_node(stage):
        def node(state: State):
            if stage in state["outputs"]:
                errors = validate_stage(stage, state["outputs"][stage], state["case"], state["outputs"])
                if errors:
                    return {"errors": [f"{stage}: {e}" for e in errors], "status": "incompleto"}
                return {}
            payload = stage_payload(stage, state["case"], state["outputs"])
            key = digest({"workflow": fingerprint, "stage": stage, "payload": payload,
                          "sources": state["case"]["source_fingerprints"]})
            path = stage_dir / stage / f"{key}.json"
            model = MODELS[stage]
            cached = path.exists()
            if cached:
                record = read_json(path)
                if record["key"] != key:
                    raise ValueError("Caché inconsistente")
            else:
                # GlobalFailure y BudgetStop se propagan para detener el lote.
                from .provider import GlobalFailure
                try:
                    raw, meta = provider.generate(stage, key, PROMPTS[stage], payload, response_schema(stage))
                    try:
                        parsed = model.model_validate_json(raw)
                        output = parsed.model_dump(mode="json")
                        errors = validate_stage(stage, output, state["case"], state["outputs"])
                    except (ValidationError, json.JSONDecodeError):
                        output, errors = None, ["La respuesta no cumple el contrato Pydantic"]
                    record = {"key": key, "stage": stage, "output": output,
                              "metadata": meta, "errors": errors,
                              "raw_output": raw if errors else None}
                except (GlobalFailure, BudgetStop) as exc:
                    return {"errors": [f"{stage}: {exc}"], "status": "interrumpido", "stop_batch": True}
                except StageFailure as exc:
                    record = {"key": key, "stage": stage, "output": None,
                              "metadata": {}, "errors": [str(exc)], "raw_output": None}
                atomic_json(path, record)
            errors = record["errors"]
            if record["output"] is not None and not errors:
                errors = validate_stage(stage, record["output"], state["case"], state["outputs"])
            meta = {**state["metadata"], stage: {**record["metadata"], "cached": cached, "key": key}}
            if errors:
                return {"errors": [f"{stage}: {e}" for e in errors], "metadata": meta, "status": "incompleto"}
            return {"outputs": {**state["outputs"], stage: record["output"]}, "metadata": meta}
        return node

    def finish(state):
        return {"status": "completado"}

    graph = StateGraph(State)
    stages = list(MODELS)
    for stage in stages:
        graph.add_node(stage, make_node(stage))
    graph.add_node("finalizar", finish)
    graph.add_edge(START, stages[0])
    for index, stage in enumerate(stages):
        following = stages[index + 1] if index + 1 < len(stages) else "finalizar"
        graph.add_conditional_edges(stage, lambda s: "stop" if s["errors"] else "next",
                                    {"stop": END, "next": following})
    graph.add_edge("finalizar", END)
    return graph.compile()


def process_case(graph, case, recovered=None):
    import copy
    outputs = copy.deepcopy((recovered or {}).get("outputs", {}))
    metadata = copy.deepcopy((recovered or {}).get("metadata", {}))
    # Solo un prefijo válido puede alimentar etapas posteriores.
    gap = False
    for stage in MODELS:
        if stage not in outputs:
            gap = True
        elif gap:
            raise ValueError("Reanudación con etapas fuera de orden")
    state = graph.invoke({"case": case, "outputs": outputs, "metadata": metadata, "errors": [],
                          "status": "en_proceso", "stop_batch": False})
    reasons = review_reasons(case, state["outputs"]) + state["errors"]
    response = state["outputs"].get("respuesta")
    return {"radicado": case["radicado"], "development_id": case["development_id"],
            "status": state["status"], "outputs": state["outputs"], "metadata": state["metadata"],
            "errors": state["errors"], "requires_review": bool(reasons), "review_reasons": reasons,
            "draft": "BORRADOR PARA REVISION\n\n" + "\n\n".join(p["texto"] for p in response["parrafos"])
                     if response else None,
            "human_review": None, "stop_batch": state["stop_batch"]}
