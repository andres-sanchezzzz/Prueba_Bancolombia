"""SDK OpenAI, salida estricta, recibos recuperables y reintentos explícitos."""
import time
from decimal import Decimal

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from .budget import BudgetStop
from .storage import atomic_json, read_json


class StageFailure(RuntimeError):
    pass


class GlobalFailure(StageFailure):
    pass


def validate_config(config):
    if config["model"] != "gpt-5.6-luna":
        raise ValueError("Otro modelo requiere verificar y configurar sus tarifas explícitamente")
    if config["reasoning_effort"] not in {"none", "low", "medium"}:
        raise ValueError("Esfuerzo de razonamiento no previsto en este primer flujo")
    if set(config["max_output_tokens"]) != {"clasificacion", "investigacion", "respuesta"}:
        raise ValueError("Faltan topes de salida por etapa")
    if any(not isinstance(v, int) or not 256 <= v <= 8000 for v in config["max_output_tokens"].values()):
        raise ValueError("Topes de salida fuera del rango de esta prueba")
    if not 0 <= config["max_explicit_retries"] <= 1:
        raise ValueError("Como máximo un reintento explícito")
    if not 10 <= config["timeout_seconds"] <= 180:
        raise ValueError("Timeout fuera del rango previsto")
    for key, minimum in [("input_usd_per_million", ".20"), ("output_usd_per_million", "1.20"),
                         ("cache_write_multiplier", "1.25")]:
        if not Decimal(config[key]).is_finite() or Decimal(config[key]) < Decimal(minimum):
            raise ValueError(f"Tarifa no válida: {key}")


class OpenAIProvider:
    def __init__(self, config, budget, receipts_dir, api_key=None, client=None):
        validate_config(config)
        self.config, self.budget, self.receipts_dir = config, budget, receipts_dir
        # Fijar endpoint evita redirecciones involuntarias por OPENAI_BASE_URL.
        self.client = client or OpenAI(api_key=api_key, base_url="https://api.openai.com/v1",
            max_retries=0, timeout=config["timeout_seconds"])

    def generate(self, stage, request_key, instructions, payload, schema):
        from .storage import canonical
        # Un segundo intento puede tener recibo aunque el primero sea incierto.
        # Recuperarlo antes de decidir si una llamada anterior bloquea la etapa.
        for attempt in range(1 + self.config["max_explicit_retries"]):
            call_id = f"{request_key}-{attempt}"
            receipt_path = self.receipts_dir / f"{call_id}.json"
            if receipt_path.exists():
                if call_id not in self.budget.data["calls"]:
                    raise BudgetStop("Recibo sin entrada contable; reconciliar manualmente")
                return self._finish(call_id, read_json(receipt_path))
        request = {"model": self.config["model"], "instructions": instructions,
                   "input": [{"role": "user", "content": canonical(payload)}],
                   "reasoning": {"effort": self.config["reasoning_effort"]},
                   "text": {"format": {"type": "json_schema", "name": stage,
                                       "strict": True, "schema": schema}},
                   "truncation": "disabled"}
        output_cap = self.config["max_output_tokens"][stage]
        for attempt in range(1 + self.config["max_explicit_retries"]):
            call_id = f"{request_key}-{attempt}"
            receipt_path = self.receipts_dir / f"{call_id}.json"
            entry = self.budget.data["calls"].get(call_id)
            if receipt_path.exists():
                receipt = read_json(receipt_path)
                if not entry:
                    raise BudgetStop("Recibo sin entrada contable; reconciliar manualmente")
                return self._finish(call_id, receipt)
            if entry:
                # Reiniciar tras timeout/cierre no debe producir otra llamada silenciosa.
                raise StageFailure("Llamada anterior sin recibo; reserva conservada, requiere revisión")
            try:
                count = self.client.responses.input_tokens.count(**request).input_tokens
            except (APIConnectionError, APIStatusError) as exc:
                raise GlobalFailure(f"No se pudo contar entrada: {type(exc).__name__}") from None
            # Margen por encapsulado; mantener por debajo de la tarifa de contexto largo.
            self.budget.reserve(call_id, count + 1024, output_cap,
                                {"request_key": request_key, "stage": stage, "attempt": attempt + 1})
            started = time.perf_counter()
            try:
                response = self.client.responses.create(**request, max_output_tokens=output_cap,
                    store=False, service_tier="default")
            except (APIConnectionError, APIStatusError) as exc:
                self.budget.uncertain(call_id, type(exc).__name__)
                code = getattr(exc, "status_code", None)
                transient = isinstance(exc, (APIConnectionError, APITimeoutError)) or code in {408, 429, 500, 502, 503, 504}
                if code in {400, 401, 403, 404, 422}:
                    raise GlobalFailure(f"Acceso o petición rechazada: {type(exc).__name__} ({code})") from None
                if transient and attempt < self.config["max_explicit_retries"]:
                    time.sleep(1)
                    continue
                raise StageFailure(f"Error de proveedor: {type(exc).__name__}; reserva conservada") from None
            receipt = {"response": response.model_dump(mode="json"),
                       "output_text": response.output_text,
                       "latency_seconds": round(time.perf_counter() - started, 3)}
            # El recibo precede a liquidación y validación: permite recuperar sin pagar otra vez.
            atomic_json(receipt_path, receipt)
            return self._finish(call_id, receipt)
        raise StageFailure("Intentos agotados")

    def _finish(self, call_id, receipt):
        response = receipt["response"]
        usage = response.get("usage")
        if not usage:
            self.budget.uncertain(call_id, "missing_usage")
            raise GlobalFailure("Respuesta sin consumo reportado; detener para reconciliar")
        self.budget.settle(call_id, usage, response["id"])
        if response.get("status") != "completed":
            raise StageFailure(f"Respuesta no completada: {response.get('status')}")
        if not receipt["output_text"].strip():
            raise StageFailure("Respuesta vacía o rechazo del proveedor")
        return receipt["output_text"], {"response_id": response["id"], "usage": usage,
            "model_returned": response.get("model"), "latency_seconds": receipt["latency_seconds"],
            "call_id": call_id}
