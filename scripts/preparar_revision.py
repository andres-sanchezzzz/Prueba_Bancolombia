"""Prepare reproducible development-review inputs without calling any model.

This is a directed development sample, not a random or representative test set.
It preserves source values and every matching customer row for human review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import openpyxl


PROJECT = Path(__file__).resolve().parents[1]
RAD_FILE = "Informacion_Radicado_PTecnica.xlsx"
CLIENT_FILE = "Informacion_Cliente_PTecnica.xlsx"

# Fixed selection after inspecting the supplied sources. These are observable
# selection conditions, not predicted labels or gold answers. They are omitted
# from the reviewer workbook to avoid influencing human answers.
SELECTION = [
    (3, "Solicitud breve con periodos enmascarados"),
    (4, "Historial extenso con fechas y respuestas previas"),
    (5, "Reclamacion sobre efectivo con valores enmascarados"),
    (19, "Dos creditos candidatos para la misma identidad"),
    (28, "Pantalla de producto sin una peticion explicita"),
    (56, "Nota literal NULL"),
    (68, "Referencia explicita a gestion en otro radicado"),
    (73, "Varias transacciones cuestionadas"),
    (76, "Solicitud de soportes de varios movimientos"),
    (88, "Actuacion documentada posterior a la solicitud"),
    (104, "Expediente mixto y varias solicitudes"),
    (117, "Reasignacion interna y necesidad del cliente"),
    (128, "Nota extensa con explicacion previa y cifras"),
    (155, "Bloques repetidos y respuesta en otro expediente"),
    (183, "Reenvio solicitado y varias filas de cliente"),
    (185, "Informacion incompleta y actuaciones posteriores"),
    (217, "Solicitud multiple y detalle faltante"),
    (233, "Solicitud y restriccion documentada en investigacion"),
    (257, "Problema del producto y dificultad de autenticacion"),
    (275, "Consulta con parametros financieros numericos"),
]


def read_rows(path: Path, expected_sheet: str) -> tuple[list[str], list[dict]]:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=False)
    try:
        sheet = workbook[expected_sheet]
        records = iter(sheet.iter_rows(values_only=True))
        headers = list(next(records))
        if len(set(headers)) != len(headers) or any(not h for h in headers):
            raise ValueError(f"Invalid source headers in {path.name}")
        rows = []
        for row_number, values in enumerate(records, 2):
            if all(v is None for v in values):
                continue
            row = dict(zip(headers, values, strict=True))
            row["source_row"] = row_number
            rows.append(row)
        return headers, rows
    finally:
        workbook.close()


def identity(row: dict) -> tuple[str, str]:
    # Source IDs are identifiers, not quantities; preserve signs and spelling.
    return str(row["descrip_documento"]).strip(), str(row["numero_de_ident"]).strip()


def fingerprint(path: Path) -> dict:
    content = path.read_bytes()
    return {"file": path.name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT / "revision" / "desarrollo.json")
    args = parser.parse_args()
    rad_path, client_path = PROJECT / RAD_FILE, PROJECT / CLIENT_FILE
    fingerprints = [fingerprint(rad_path), fingerprint(client_path)]
    source_manifest = json.loads((PROJECT / "INSUMOS.json").read_text(encoding="utf-8"))
    expected = {f["path"]: f["sha256"] for f in source_manifest["files"]}
    for source in fingerprints:
        if source["sha256"] != expected[source["file"]]:
            raise ValueError(f"Source changed: {source['file']}. Review the selection before regenerating.")

    rad_headers, radicados = read_rows(rad_path, "Informacion_AQR")
    client_headers, clients = read_rows(client_path, "Informacion_Cliente")
    if len(radicados) != 275 or len({str(r['numero_de_radicado']) for r in radicados}) != 275:
        raise ValueError("Unexpected source population or duplicate radicado IDs")
    by_row = {r["source_row"]: r for r in radicados}
    by_identity: dict[tuple[str, str], list[dict]] = {}
    for row in clients:
        by_identity.setdefault(identity(row), []).append(row)

    cases = []
    selected_keys = set()
    for i, (source_row, condition) in enumerate(SELECTION, 1):
        record = by_row[source_row]
        key = identity(record)
        if key in selected_keys:
            raise ValueError("This development selection expects twenty distinct customers")
        selected_keys.add(key)
        candidates = by_identity.get(key, [])
        if not candidates:
            raise ValueError(f"No customer candidate for source row {source_row}")
        cases.append({
            "case_id": f"D{i:02}",
            "radicado": str(record["numero_de_radicado"]),
            "selection_condition": condition,
            "radicado_source": record,
            "customer_candidates": candidates,
            "human_review": {
                "tipologia": None,
                "motivo_en_tus_palabras": None,
                "evidencia": None,
                "causa_sustentada": None,
                "datos_pendientes": None,
                "requiere_revision": None,
                "observaciones": None,
            },
        })

    excluded = [str(r["numero_de_radicado"]) for r in radicados if identity(r) in selected_keys]
    payload = {
        "schema_version": 1,
        "purpose": "development_human_review",
        "selection_method": "directed_diverse_fixed_source_rows",
        "not_representative_test_sample": True,
        "source_fingerprints": fingerprints,
        "source_headers": {"radicados": rad_headers, "clientes": client_headers},
        "development_case_count": len(cases),
        "excluded_from_final_test_by_customer": excluded,
        "similarity_review_pending_before_final_test_selection": True,
        "final_test_selected": False,
        "cases": cases,
    }
    # Detect source changes during reading as well as against the initial manifest.
    if fingerprints != [fingerprint(rad_path), fingerprint(client_path)]:
        raise ValueError("Source files changed during reading")
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing review data: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"cases": len(cases), "distinct_customers": len(selected_keys),
                      "excluded_test_cases_by_customer": len(excluded),
                      "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
