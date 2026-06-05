#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"


@dataclass
class ProceedApprovalResult:
    approval_path: Path


class ProceedGateApprover:
    def __init__(self, repo_root: Path, proceed_gate: Path, out: Path, decision: str, approver: str, notes: str) -> None:
        self.repo_root = repo_root
        self.proceed_gate = proceed_gate
        self.out = out
        self.decision = decision
        self.approver = approver
        self.notes = notes
        self.issues: list[Issue] = []

    def error(self, path: Path | str, message: str) -> None:
        self.issues.append(Issue(str(path), message))

    def load_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.error(path, "file does not exist")
        except json.JSONDecodeError as exc:
            self.error(path, f"invalid JSON: {exc}")
        return None

    def approve(self) -> ProceedApprovalResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.proceed_gate)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        gate = self.load_json(self.proceed_gate)
        if not isinstance(gate, dict):
            return None
        if gate.get("kind") != "proceed_gate_package":
            self.error(self.proceed_gate, "approval requires a proceed_gate_package document")
            return None
        if gate.get("status") != "ready_for_user_review":
            self.error(self.proceed_gate, "approval requires proceed gate status ready_for_user_review")
            return None
        if self.decision not in gate.get("decision_options", []):
            self.error(self.proceed_gate, f"decision {self.decision!r} is not available in proceed gate options")
            return None

        approval = self.build_approval(gate)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.out, approval)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None
        return ProceedApprovalResult(approval_path=self.out)

    def build_approval(self, gate: dict[str, Any]) -> dict[str, Any]:
        spec_id = str(gate["spec_id"])
        decision_suffix = "detail" if self.decision == "detail_upgrade" else "proceed"
        approval = {
            "schema_version": SCHEMA_VERSION,
            "kind": "proceed_approval",
            "id": f"{spec_id}.{decision_suffix}_approval",
            "spec_id": spec_id,
            "proceed_gate_id": str(gate["id"]),
            "decision": self.decision,
            "approved_next_maturity": "detail_cad",
            "approver": self.approver,
            "approved_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "locked_layout_facts": [str(item) for item in gate.get("locked_layout_facts", [])],
            "notes": self.notes,
            "extensions": {
                "approver": "tools/approve_proceed_gate.py",
                "proceed_gate": str(self.proceed_gate),
            },
        }
        return approval


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record explicit user approval for a Zen CAD proceed gate package.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--proceed-gate", type=Path, required=True, help="Proceed gate package JSON.")
    parser.add_argument("--out", type=Path, required=True, help="Output proceed approval JSON path.")
    parser.add_argument("--decision", choices=["proceed", "detail_upgrade"], default="proceed", help="Approved proceed decision.")
    parser.add_argument("--approver", default="user", help="Approver label to record in the approval artifact.")
    parser.add_argument("--notes", default="", help="Optional approval notes.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    approver = ProceedGateApprover(args.repo_root, args.proceed_gate, args.out, args.decision, args.approver, args.notes)
    result = approver.approve()
    if approver.issues:
        for issue in approver.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("proceed approval failed", file=sys.stderr)
        return 1
    print(f"Proceed approval: {result.approval_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
