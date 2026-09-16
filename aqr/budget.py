"""Contabilidad conservadora en microdólares enteros; incluye llamadas inciertas."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING

from .storage import atomic_json, read_json


class BudgetStop(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def cost_micro(input_tokens, output_tokens, config):
    # Cobrar toda entrada a tarifa de escritura de caché evita asumir descuentos.
    # No es una factura: es una cota contable conservadora del consumo reportado.
    value = (Decimal(input_tokens) * Decimal(config["input_usd_per_million"])
             * Decimal(config["cache_write_multiplier"])
             + Decimal(output_tokens) * Decimal(config["output_usd_per_million"]))
    return int(value.to_integral_value(rounding=ROUND_CEILING))


class Budget:
    """Usar bajo project_lock; un único ledger para todos los experimentos."""

    def __init__(self, path, config):
        self.path, self.config = path, config
        requested_cap = int(Decimal(config["budget_usd"]) * 1_000_000)
        if not 0 < requested_cap <= 3_000_000:
            raise ValueError("El presupuesto debe ser positivo y no superar USD 3")
        if path.exists():
            self.data = read_json(path)
            if self.data["cap_micro_usd"] != requested_cap:
                raise BudgetStop("El límite no se cambia en una contabilidad existente")
        else:
            if any(path.parent.glob("stages/**/*.json")) or any(path.parent.glob("receipts/*.json")):
                raise BudgetStop("Hay resultados pero falta el ledger; no reiniciar el gasto a cero")
            self.data = {"schema_version": 1, "cap_micro_usd": requested_cap, "calls": {}}
            atomic_json(path, self.data)
        if self.total() > requested_cap:
            raise BudgetStop("Consumo contabilizado superior al límite; revisar antes de continuar")

    def total(self):
        return sum(item["charged_micro_usd"] for item in self.data["calls"].values())

    def reserve(self, call_id, input_bound, output_cap, metadata):
        if call_id in self.data["calls"]:
            raise BudgetStop("Llamada ya registrada; no repetir una reserva")
        if not 0 <= input_bound <= 200_000 or output_cap <= 0:
            raise BudgetStop("Fuera del rango de tokens permitido por la tarifa configurada")
        amount = cost_micro(input_bound, output_cap, self.config)
        if self.total() + amount > self.data["cap_micro_usd"]:
            raise BudgetStop("Presupuesto insuficiente para reservar esta llamada")
        self.data["calls"][call_id] = {"state": "reserved", "created_at": now(),
            "input_bound": input_bound, "output_cap": output_cap,
            "reserved_micro_usd": amount, "charged_micro_usd": amount, **metadata}
        atomic_json(self.path, self.data)

    def uncertain(self, call_id, error_type):
        item = self.data["calls"][call_id]
        item.update(state="uncertain", error_type=error_type)
        atomic_json(self.path, self.data)

    def settle(self, call_id, usage, response_id):
        item = self.data["calls"][call_id]
        if item["state"] == "settled":
            return
        amount = cost_micro(usage["input_tokens"], usage["output_tokens"], self.config)
        item.update(state="settled", usage=usage, response_id=response_id,
                    charged_micro_usd=amount, settled_at=now())
        atomic_json(self.path, self.data)
        if (usage["input_tokens"] > item["input_bound"]
                or usage["output_tokens"] > item["output_cap"]
                or amount > item["reserved_micro_usd"]):
            raise BudgetStop("El proveedor excedió la reserva; detener y reconciliar tarifas/consumo")

    def summary(self):
        items = list(self.data["calls"].values())
        settled = sum(c["charged_micro_usd"] for c in items if c["state"] == "settled")
        return {"cap_usd": self.data["cap_micro_usd"] / 1_000_000,
                "accounted_upper_usd": settled / 1_000_000,
                "reserved_or_uncertain_usd": (self.total() - settled) / 1_000_000,
                "remaining_usd": (self.data["cap_micro_usd"] - self.total()) / 1_000_000,
                "generation_attempts": len(items),
                "note": "Contabilidad conservadora, no factura del proveedor"}
