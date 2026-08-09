"""Benchmark Evaluator & Telemetry Analysis Engine for Emergence Lab."""

from typing import List, Dict, Any
from emergence_lab.domain.events import Event

class BenchmarkMetrics:
    def __init__(self, run_id: str, model_name: str, harness_mode: str):
        self.run_id = run_id
        self.model_name = model_name
        self.harness_mode = harness_mode
        self.total_turns = 0
        self.valid_turns = 0
        self.repaired_turns = 0
        self.failed_turns = 0
        self.total_prompt_tokens = 0
        self.total_eval_tokens = 0
        self.total_duration_ms = 0.0
        self.questions_posed = 0
        self.speech_lengths = []

    def compute_summary(self) -> Dict[str, Any]:
        avg_speech_len = sum(self.speech_lengths) / len(self.speech_lengths) if self.speech_lengths else 0.0
        target_fidelity = (self.valid_turns + self.repaired_turns) / max(1, self.total_turns) * 100.0
        tokens_per_sec = (self.total_eval_tokens / (self.total_duration_ms / 1000.0)) if self.total_duration_ms > 0 else 0.0
        quality_score = (avg_speech_len * 0.4) + (self.questions_posed * 10.0) + (target_fidelity * 0.5)
        efficiency_ratio = quality_score / max(1.0, (self.total_duration_ms / 1000.0))

        return {
            "run_id": self.run_id,
            "model_name": self.model_name,
            "harness_mode": self.harness_mode,
            "total_turns": self.total_turns,
            "target_fidelity_pct": round(target_fidelity, 1),
            "valid_turns": self.valid_turns,
            "repaired_turns": self.repaired_turns,
            "failed_turns": self.failed_turns,
            "avg_speech_length_chars": round(avg_speech_len, 1),
            "questions_posed": self.questions_posed,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_eval_tokens": self.total_eval_tokens,
            "total_duration_sec": round(self.total_duration_ms / 1000.0, 2),
            "tokens_per_sec": round(tokens_per_sec, 1),
            "quality_score": round(quality_score, 1),
            "compute_efficiency_ratio": round(efficiency_ratio, 2)
        }

import json

def evaluate_run(events: List[Dict[str, Any]], model_name: str, harness_mode: str) -> BenchmarkMetrics:
    run_id = events[0].get("run_id", "unknown") if events else "unknown"
    metrics = BenchmarkMetrics(run_id=run_id, model_name=model_name, harness_mode=harness_mode)

    for ev in events:
        if ev.get("event_type") in ["action:speak", "action:synthesize"]:
            metrics.total_turns += 1
            payload = ev.get("payload", {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {}

            speech = payload.get("speech", {}) or payload.get("synthesis", {})
            if isinstance(speech, dict):
                msg = speech.get("message", "")
            else:
                msg = str(speech)
            
            metrics.speech_lengths.append(len(msg))
            if "?" in msg:
                metrics.questions_posed += 1

            telemetry = ev.get("telemetry") or payload.get("telemetry")
            if isinstance(telemetry, dict):
                status = telemetry.get("validation_status", "valid")
                if status == "valid":
                    metrics.valid_turns += 1
                elif status == "repaired":
                    metrics.repaired_turns += 1
                else:
                    metrics.failed_turns += 1

                metrics.total_prompt_tokens += telemetry.get("prompt_tokens") or 0
                metrics.total_eval_tokens += telemetry.get("eval_tokens") or 0
                metrics.total_duration_ms += telemetry.get("duration_ms") or 0.0
            else:
                metrics.valid_turns += 1

    return metrics
