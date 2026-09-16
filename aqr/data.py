"""Lectura completa, identidad opaca y cruces sin seleccionar candidatos arbitrarios."""
import json
from collections import defaultdict
from pathlib import Path

from scripts.preparar_revision import CLIENT_FILE, RAD_FILE, fingerprint, identity, read_rows


def missing(value):
    return value is None or (isinstance(value, str) and value.strip().upper() in {"", "NULL"})


def source_text(value):
    if value is None:
        return ""
    return str(value)


def load_cases(root: Path) -> list[dict]:
    expected = json.loads((root / "INSUMOS.json").read_text(encoding="utf-8"))
    hashes = {f["path"]: f["sha256"] for f in expected["files"]}
    files = [root / RAD_FILE, root / CLIENT_FILE]
    before = [fingerprint(p) for p in files]
    for item in before:
        if hashes.get(item["file"]) != item["sha256"]:
            raise ValueError(f"Fuente modificada: {item['file']}")
    _, radicados = read_rows(files[0], "Informacion_AQR")
    _, clientes = read_rows(files[1], "Informacion_Cliente")
    if len(radicados) != 275 or len({str(r['numero_de_radicado']) for r in radicados}) != 275:
        raise ValueError("Se esperaban 275 radicados únicos")
    grouped = defaultdict(list)
    for row in clientes:
        if missing(row["descrip_documento"]) or missing(row["numero_de_ident"]):
            raise ValueError("Cliente sin identidad utilizable")
        grouped[identity(row)].append(row)
    development = json.loads((root / "revision/desarrollo.json").read_text(encoding="utf-8"))
    dev_ids = {c["radicado"]: c["case_id"] for c in development["cases"]}
    result = []
    for row in radicados:
        if missing(row["descrip_documento"]) or missing(row["numero_de_ident"]):
            raise ValueError("Radicado sin identidad utilizable")
        radicado = str(row["numero_de_radicado"])
        candidates = grouped.get(identity(row), [])
        sources = []
        for origin, filename, sheet, records in [
            ("radicado", RAD_FILE, "Informacion_AQR", [row]),
            ("cliente", CLIENT_FILE, "Informacion_Cliente", candidates),
        ]:
            for record in records:
                for field, value in record.items():
                    if field == "source_row":
                        continue
                    sources.append({"id": f"{origin}:{record['source_row']}:{field}",
                                    "archivo": filename, "hoja": sheet, "fila": record["source_row"],
                                    "campo": field, "texto": source_text(value), "ausente": missing(value)})
        conflicts = {}
        if candidates:
            for field in candidates[0]:
                if field in {"source_row", "numero_de_ident", "descrip_documento"}:
                    continue
                values = sorted({source_text(c[field]) for c in candidates if not missing(c[field])})
                if len(values) > 1:
                    conflicts[field] = values
        result.append({"radicado": radicado, "development_id": dev_ids.get(radicado),
                       "radicado_source": row, "customer_candidates": candidates,
                       "sources": sources, "join": {"candidate_count": len(candidates),
                       "ambiguous": len(candidates) > 1, "conflicts": conflicts},
                       "source_fingerprints": before})
    if before != [fingerprint(p) for p in files]:
        raise ValueError("Las fuentes cambiaron durante la lectura")
    return result
