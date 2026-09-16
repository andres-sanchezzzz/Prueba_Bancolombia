"""Controles deterministas de estructura y referencias, no un juez semántico."""
from .schemas import Clasificacion, Investigacion, Respuesta


def validate_stage(stage, output, case, previous):
    problems = []
    sources = {s["id"]: s for s in case["sources"]}

    def check_cites(cites, label):
        for cite in cites:
            source = sources.get(cite.fuente_id)
            if cite.uso == "ausencia":
                if stage != "investigacion" or source is None or not source["ausente"] or cite.texto != source["texto"]:
                    problems.append(f"{label}: referencia de ausencia inválida ({cite.fuente_id})")
            elif (source is None or source["ausente"] or not cite.texto.strip()
                    or cite.texto not in source["texto"]):
                problems.append(f"{label}: cita inexistente, vacía o no literal ({cite.fuente_id})")

    if stage == "clasificacion":
        item = Clasificacion.model_validate(output)
        check_cites(item.evidencia, "clasificacion")
        if any(not c.fuente_id.startswith("radicado:") for c in item.evidencia):
            problems.append("Clasificación respaldada por una fuente distinta del radicado")
        if not item.causalidad.strip() or not item.justificacion.strip():
            problems.append("Causalidad o justificación vacía")
        if not item.evidencia and not item.requiere_revision:
            problems.append("Clasificación sin evidencia requiere revisión")
        if item.asignacion_forzada and not item.requiere_revision:
            problems.append("Asignación forzada sin revisión explícita")
    elif stage == "investigacion":
        item = Investigacion.model_validate(output)
        ids = [h.id for h in item.hallazgos]
        if len(ids) != len(set(ids)) or any(not i.strip() for i in ids):
            problems.append("IDs de hallazgos vacíos o repetidos")
        for h in item.hallazgos:
            check_cites(h.evidencia, h.id)
            if not h.evidencia or not h.descripcion.strip():
                problems.append(f"{h.id}: hallazgo sin descripción o evidencia")
        causes = {h.id for h in item.hallazgos if h.tipo == "causa_documentada"}
        if set(item.causa_documentada_ids) != causes:
            problems.append("Referencias de causa documentada inconsistentes")
    else:
        item = Respuesta.model_validate(output)
        findings = {h["id"] for h in previous["investigacion"]["hallazgos"]}
        pending = previous["investigacion"]["datos_pendientes"]
        if not item.parrafos:
            problems.append("Borrador vacío")
        used_pending = set()
        for p in item.parrafos:
            if not p.texto.strip():
                problems.append("Párrafo vacío")
            if not set(p.evidencia_ids) <= findings:
                problems.append("Referencia a un hallazgo inexistente")
            if any(i < 0 or i >= len(pending) for i in p.pendiente_indices):
                problems.append("Referencia a un pendiente inexistente")
            if p.tipo == "hecho" and not p.evidencia_ids:
                problems.append("Párrafo factual sin evidencia")
            if p.tipo == "pendiente" and not p.pendiente_indices:
                problems.append("Párrafo pendiente sin referencia")
            if p.tipo == "cortesia" and (p.evidencia_ids or p.pendiente_indices):
                problems.append("Cortesía con referencias factuales: revisar tipo")
            used_pending.update(p.pendiente_indices)
        if set(range(len(pending))) - used_pending:
            problems.append("Hay pendientes de investigación omitidos en el borrador")
    if item.requiere_revision and not item.razones_revision:
        problems.append("Revisión requerida sin razón explícita")
    return problems


def review_reasons(case, outputs):
    reasons = []
    if not case["customer_candidates"]:
        reasons.append("Sin coincidencia de cliente")
    if case["join"]["ambiguous"]:
        reasons.append("Varios candidatos de cliente; correspondencia no desambiguada")
    if case["join"]["conflicts"]:
        reasons.append("Conflictos de cliente: " + ", ".join(case["join"]["conflicts"]))
    for value in outputs.values():
        reasons.extend(value.get("razones_revision", []))
    if outputs.get("clasificacion", {}).get("asignacion_forzada"):
        reasons.append("Asignación forzada fuera de encaje claro")
    if outputs.get("investigacion", {}).get("datos_pendientes"):
        reasons.append("Información pendiente para responder completamente")
    return list(dict.fromkeys(reasons))
