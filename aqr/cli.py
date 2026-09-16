"""Comandos reproducibles; prepare nunca llama a un proveedor."""
import argparse
import getpass
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Esta prueba conserva auditoría local; no activa callbacks de trazas de terceros.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from .budget import Budget, BudgetStop
from .data import load_cases
from .provider import GlobalFailure, OpenAIProvider, validate_config
from .storage import atomic_json, digest, project_lock, read_json
from .workflow import build_graph, process_case, workflow_fingerprint

ROOT = Path(__file__).resolve().parents[1]


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="AQR: clasificación, investigación y borradores")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        command = sub.add_parser(name)
        command.add_argument("--scope", choices=["development", "all"], default="development")
        command.add_argument("--limit", type=int)
        command.add_argument("--config", type=Path, default=ROOT / "config/openai.json")
        if name == "run":
            command.add_argument("--ask-key", action="store_true", help="Pedir clave oculta solo en esta terminal")
    sub.add_parser("budget")
    export = sub.add_parser("export")
    export.add_argument("--run", type=Path, required=True, help="JSON de ejecución")
    export.add_argument("--output", type=Path, required=True)
    review = sub.add_parser("import-review")
    review.add_argument("--run", type=Path, required=True)
    review.add_argument("--workbook", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "import-review":
        from .review import import_review
        result = import_review(args.workbook, read_json(args.run), args.output)
        emit({"reviewed_count": result["reviewed_count"], "output": str(args.output.resolve())})
        return 0
    if args.command == "export":
        from .export import export_workbook
        export_workbook(read_json(args.run), load_cases(ROOT), args.output)
        emit({"workbook": str(args.output.resolve())})
        return 0
    if args.command == "budget":
        path = ROOT / "runs/budget.json"
        if not path.exists():
            emit({"generation_attempts": 0, "accounted_upper_usd": 0, "reserved_or_uncertain_usd": 0})
        else:
            with project_lock(ROOT / "runs/.lock"):
                emit(Budget(path, read_json(ROOT / "config/openai.json")).summary())
        return 0
    config = read_json(args.config)
    validate_config(config)
    all_cases = load_cases(ROOT)
    cases = [c for c in all_cases if args.scope == "all" or c["development_id"]]
    if args.limit is not None:
        if args.limit <= 0:
            parser.error("--limit debe ser positivo")
        cases = cases[:args.limit]
    fingerprint = workflow_fingerprint(config)
    if args.command == "prepare":
        summary = {"scope": args.scope, "case_count": len(cases), "total_available": len(all_cases),
                   "generation_calls_if_uncached": 3 * len(cases),
                   "ambiguous_cases": sum(c["join"]["ambiguous"] for c in cases),
                   "cases_with_conflicts": sum(bool(c["join"]["conflicts"]) for c in cases),
                   "workflow_fingerprint": fingerprint, "provider_called": False,
                   "api_key_available": bool(os.environ.get("OPENAI_API_KEY"))}
        target = ROOT / "outputs" / f"preparacion_{args.scope}.json"
        atomic_json(target, {"summary": summary, "cases": cases})
        emit({**summary, "output": str(target)})
        return 0
    key = os.environ.get("OPENAI_API_KEY")
    if args.ask_key:
        key = getpass.getpass("Clave OpenAI (oculta; no se guardará): ").strip()
    if not key:
        emit({"error": "Falta OPENAI_API_KEY. Ejecuta run --ask-key en tu terminal; no envíes la clave al chat.",
              "provider_called": False})
        return 2
    # Un ledger compartido entre desarrollo, ejecución final y futuros experimentos.
    with project_lock(ROOT / "runs/.lock"):
        budget = Budget(ROOT / "runs/budget.json", config)
        provider = OpenAIProvider(config, budget, ROOT / "runs/receipts", api_key=key)
        graph = build_graph(provider, ROOT / "runs/stages", fingerprint)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = ROOT / "runs" / f"{run_id}.json"
        run = {"schema_version": 1, "run_id": run_id, "scope": args.scope,
               "workflow_fingerprint": fingerprint, "config": config,
               "case_ids": [c["radicado"] for c in cases], "results": [],
               "source_fingerprints": cases[0]["source_fingerprints"],
               "status": "en_proceso", "budget": budget.summary()}
        stop_reason = None
        for i, case in enumerate(cases, 1):
            if stop_reason:
                result = {"radicado": case["radicado"], "development_id": case["development_id"],
                    "status": "no_procesado", "outputs": {}, "metadata": {}, "draft": None,
                    "errors": [stop_reason], "requires_review": True, "review_reasons": [stop_reason],
                    "human_review": None}
            else:
                try:
                    result = process_case(graph, case)
                    if result.get("stop_batch"):
                        stop_reason = "; ".join(result["errors"])
                except (BudgetStop, GlobalFailure) as exc:
                    stop_reason = str(exc)
                    result = {"radicado": case["radicado"], "development_id": case["development_id"],
                        "status": "interrumpido", "outputs": {}, "metadata": {}, "draft": None,
                        "errors": [stop_reason], "requires_review": True, "review_reasons": [stop_reason],
                        "human_review": None}
            run["results"].append(result)
            run["budget"] = budget.summary()
            atomic_json(path, run)
            print(f"{i}/{len(cases)}: {result['status']}", flush=True)
        run["status"] = "completado" if all(r["status"] == "completado" for r in run["results"]) else "con_pendientes"
        run["counts"] = dict(Counter(r["status"] for r in run["results"]))
        atomic_json(path, run)
        emit({"run": str(path), "status": run["status"], "counts": run["counts"], "budget": run["budget"]})
        return 0 if run["status"] == "completado" else 1


if __name__ == "__main__":
    raise SystemExit(main())
