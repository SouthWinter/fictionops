from __future__ import annotations

import json
import math
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from .agent_exec import AgentExecReport, build_agent_exec
from .agent_revision_runtime import utc_now
from .agent_trajectory import append_trajectory


MODEL_BUDGET_SCHEMA = "fictionops.model_execution_budget.v1"


class ModelBudgetExceeded(RuntimeError):
    """Raised before a model call that would exceed the controller budget."""


@dataclass
class ModelExecutionBudget:
    run_dir: Path
    max_calls: int
    max_runtime_seconds: int
    max_total_tokens: int | None = None
    max_cost: float | None = None
    cost_currency: str = "USD"
    started_at: str = field(default_factory=utc_now)
    records: list[dict[str, object]] = field(default_factory=list)
    prior_budget_files: list[str] = field(default_factory=list)
    prior_used_calls: int = 0
    prior_usage: dict[str, int] = field(default_factory=dict)
    prior_cost_by_currency: dict[str, float] = field(default_factory=dict)
    status: str = "active"
    _started_monotonic: float = field(default_factory=time.monotonic, repr=False)

    def __post_init__(self) -> None:
        if self.max_calls < 1:
            raise ValueError("--max-model-calls must be greater than zero")
        if self.max_runtime_seconds < 1:
            raise ValueError("--max-runtime-seconds must be greater than zero")
        if self.max_total_tokens is not None and self.max_total_tokens < 1:
            raise ValueError("--max-total-tokens must be greater than zero")
        if self.max_cost is not None and self.max_cost <= 0:
            raise ValueError("--max-cost must be greater than zero")
        self.cost_currency = self.cost_currency.strip().upper()
        if not self.cost_currency:
            raise ValueError("--cost-currency must not be empty")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.write()

    @property
    def path(self) -> Path:
        return self.run_dir / "model_budget.json"

    @property
    def used_calls(self) -> int:
        return len(self.records)

    @property
    def elapsed_seconds(self) -> float:
        return max(0.0, time.monotonic() - self._started_monotonic)

    @property
    def remaining_runtime_seconds(self) -> int:
        return max(0, math.ceil(self.max_runtime_seconds - self.elapsed_seconds))

    def payload(self, *, attempted_role: str | None = None, reason: str | None = None) -> dict[str, object]:
        segment_usage = self.usage_summary()
        cumulative_usage = {
            key: int(self.prior_usage.get(key) or 0) + int(segment_usage.get(key) or 0)
            for key in sorted(set(self.prior_usage) | set(segment_usage))
        }
        segment_cost = self.cost_summary()
        cumulative_cost = {
            key: round(float(self.prior_cost_by_currency.get(key) or 0) + float(segment_cost.get(key) or 0), 12)
            for key in sorted(set(self.prior_cost_by_currency) | set(segment_cost))
        }
        return {
            "schema": MODEL_BUDGET_SCHEMA,
            "status": self.status,
            "started_at": self.started_at,
            "updated_at": utc_now(),
            "max_calls": self.max_calls,
            "used_calls": self.used_calls,
            "remaining_calls": max(0, self.max_calls - self.used_calls),
            "prior_used_calls": self.prior_used_calls,
            "cumulative_used_calls": self.prior_used_calls + self.used_calls,
            "prior_budget_files": self.prior_budget_files,
            "segment_usage": segment_usage,
            "cumulative_usage": cumulative_usage,
            "segment_cost_by_currency": segment_cost,
            "cumulative_cost_by_currency": cumulative_cost,
            "max_runtime_seconds": self.max_runtime_seconds,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "remaining_runtime_seconds": self.remaining_runtime_seconds,
            "max_total_tokens": self.max_total_tokens,
            "remaining_total_tokens": None if self.max_total_tokens is None else max(0, self.max_total_tokens - int(cumulative_usage.get("total_tokens") or 0)),
            "max_cost": self.max_cost,
            "cost_currency": self.cost_currency,
            "remaining_cost": None if self.max_cost is None else round(max(0.0, self.max_cost - float(cumulative_cost.get(self.cost_currency) or 0)), 12),
            "attempted_role": attempted_role,
            "stop_reason": reason,
            "calls": self.records,
        }

    def usage_summary(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for record in self.records:
            telemetry = record.get("telemetry")
            usage = telemetry.get("usage") if isinstance(telemetry, dict) else None
            if not isinstance(usage, dict):
                continue
            for key, value in usage.items():
                if isinstance(value, int) and not isinstance(value, bool):
                    totals[str(key)] = totals.get(str(key), 0) + value
        return totals

    def cost_summary(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for record in self.records:
            telemetry = record.get("telemetry")
            cost = telemetry.get("cost") if isinstance(telemetry, dict) else None
            if not isinstance(cost, dict):
                continue
            currency = str(cost.get("currency") or "").upper()
            total = cost.get("total")
            if currency and isinstance(total, (int, float)) and not isinstance(total, bool):
                totals[currency] = totals.get(currency, 0.0) + float(total)
        return {key: round(value, 12) for key, value in totals.items()}

    def write(self, *, attempted_role: str | None = None, reason: str | None = None) -> None:
        self.path.write_text(
            json.dumps(self.payload(attempted_role=attempted_role, reason=reason), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def claim(self, role: str, bundle_dir: Path) -> int:
        reason = None
        cumulative_usage = self.payload().get("cumulative_usage") or {}
        cumulative_cost = self.payload().get("cumulative_cost_by_currency") or {}
        if self.used_calls >= self.max_calls:
            reason = "model_call_budget_exhausted"
        elif self.elapsed_seconds >= self.max_runtime_seconds:
            reason = "model_runtime_budget_exhausted"
        elif self.max_total_tokens is not None and int(cumulative_usage.get("total_tokens") or 0) >= self.max_total_tokens:
            reason = "model_token_budget_exhausted"
        elif self.max_cost is not None and float(cumulative_cost.get(self.cost_currency) or 0) >= self.max_cost:
            reason = "model_cost_budget_exhausted"
        if reason:
            self.status = "exhausted"
            self.write(attempted_role=role, reason=reason)
            append_trajectory(
                self.run_dir,
                kind="budget_stop",
                phase="budget_exhausted",
                actor="controller",
                observation={"reason": reason, "role": role},
                decision={"continue_model_calls": False},
                authority="controller",
            )
            raise ModelBudgetExceeded(f"{reason}; inspect {self.path}")
        call_id = self.used_calls + 1
        self.records.append(
            {
                "call_id": call_id,
                "role": role,
                "bundle_dir": str(bundle_dir.resolve()),
                "claimed_at": utc_now(),
                "status": "running",
            }
        )
        self.write()
        append_trajectory(
            self.run_dir,
            kind="model_call_started",
            phase=role,
            actor="model_worker",
            action={"role": role, "bundle_dir": str(bundle_dir.resolve())},
            model_call={"call_id": call_id, "status": "running"},
            authority="controller",
        )
        return call_id

    def finish(self, call_id: int, status: str, telemetry: dict[str, object] | None = None) -> None:
        for record in self.records:
            if int(record.get("call_id") or 0) == call_id:
                record["status"] = status
                record["finished_at"] = utc_now()
                if telemetry is not None:
                    record["telemetry"] = telemetry
                break
        self.write()
        append_trajectory(
            self.run_dir,
            kind="model_call_finished",
            phase=str(next((item.get("role") for item in self.records if int(item.get("call_id") or 0) == call_id), "model_call")),
            actor="model_worker",
            observation={"status": status},
            model_call={"call_id": call_id, "status": status, "telemetry": telemetry},
            authority="controller",
        )

    def complete(self) -> None:
        if self.status != "exhausted":
            self.status = "completed"
            self.write()


def execute_model_bundle(
    budget: ModelExecutionBudget,
    directory: Path,
    *,
    role: str,
    command: list[str],
    output_name: str,
    timeout_seconds: int,
    force: bool,
    dry_run: bool,
) -> AgentExecReport:
    call_id = budget.claim(role, directory)
    effective_timeout = min(timeout_seconds, max(1, budget.remaining_runtime_seconds))
    try:
        report = build_agent_exec(
            directory,
            command=command,
            output_name=output_name,
            timeout_seconds=effective_timeout,
            force=force,
            dry_run=dry_run,
        )
    except Exception:
        budget.finish(call_id, "failed")
        budget.status = "failed"
        budget.write(attempted_role=role, reason="model_call_failed")
        raise
    budget.finish(call_id, "completed", report.telemetry)
    return report


def start_model_budget(
    run_dir: Path,
    *,
    max_calls: int,
    max_runtime_seconds: int,
    max_total_tokens: int | None = None,
    max_cost: float | None = None,
    cost_currency: str = "USD",
    resume: bool = False,
) -> ModelExecutionBudget:
    current = run_dir / "model_budget.json"
    prior_files: list[str] = []
    prior_used = 0
    prior_usage: dict[str, int] = {}
    prior_cost: dict[str, float] = {}
    if current.exists():
        if not resume:
            raise FileExistsError(current)
        try:
            previous = json.loads(current.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"cannot resume with invalid model budget: {current}") from exc
        prior_used = int(previous.get("cumulative_used_calls") or previous.get("used_calls") or 0)
        prior_usage = {
            str(key): int(value)
            for key, value in (previous.get("cumulative_usage") or previous.get("segment_usage") or {}).items()
            if isinstance(value, int) and not isinstance(value, bool)
        }
        prior_cost = {
            str(key): float(value)
            for key, value in (previous.get("cumulative_cost_by_currency") or previous.get("segment_cost_by_currency") or {}).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        prior_files.extend(str(item) for item in previous.get("prior_budget_files") or [])
        index = 1
        while (run_dir / f"model_budget.segment{index}.json").exists():
            index += 1
        archived = run_dir / f"model_budget.segment{index}.json"
        shutil.move(str(current), str(archived))
        prior_files.append(str(archived.resolve()))
    return ModelExecutionBudget(
        run_dir=run_dir,
        max_calls=max_calls,
        max_runtime_seconds=max_runtime_seconds,
        max_total_tokens=max_total_tokens,
        max_cost=max_cost,
        cost_currency=cost_currency,
        prior_budget_files=prior_files,
        prior_used_calls=prior_used,
        prior_usage=prior_usage,
        prior_cost_by_currency=prior_cost,
    )
