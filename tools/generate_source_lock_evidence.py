#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"

PROXY_SOURCE_LOCK_REQUIREMENT = "Replace proxy with step.parts, manufacturer, datasheet, or user-provided source before final."

DEFAULT_REQUIRED_BEFORE_FINAL = [
    "Import the locked source geometry in the downstream CAD harness.",
    "Run geometry checks for required datums, axes, interfaces, and clearances.",
    "Stop if source geometry changes an approved locked layout fact.",
]

DEFAULT_CLAIMS_NOT_MADE = [
    "No rating, load capacity, torque capacity, or safety factor is claimed.",
    "No certification, compliance, price, inventory, or availability is claimed.",
    "No generated STEP geometry is certified by this evidence artifact alone.",
]


@dataclass
class SourceLockResult:
    evidence_path: Path


class SourceLockEvidenceGenerator:
    def __init__(
        self,
        repo_root: Path,
        package: Path | None,
        out: Path,
        args: argparse.Namespace,
    ) -> None:
        self.repo_root = repo_root
        self.package = package
        self.out = out
        self.args = args
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

    def generate(self) -> SourceLockResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        if self.package is not None:
            validator.validate_package(self.package)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        documents = self.load_package_documents()
        spec_id = self.resolve_spec_id(documents)
        if spec_id is None:
            return None

        interface_refs = list(self.args.interface_signature_ref or [])
        package_refs = self.resolve_layout_interface_refs(documents)
        if package_refs is None:
            return None
        if not interface_refs:
            interface_refs = package_refs

        evidence_sources = self.build_evidence_sources()
        if not evidence_sources:
            self.error("<args>", "source lock generation requires at least one evidence URL or file")
            return None

        document = self.build_document(spec_id, interface_refs, evidence_sources)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.out, document)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None
        return SourceLockResult(evidence_path=self.out)

    def load_package_documents(self) -> list[tuple[Path, dict[str, Any]]]:
        if self.package is None:
            return []
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        documents: list[tuple[Path, dict[str, Any]]] = []
        for path in paths:
            document = self.load_json(path)
            if isinstance(document, dict):
                documents.append((path, document))
        return documents

    def resolve_spec_id(self, documents: list[tuple[Path, dict[str, Any]]]) -> str | None:
        if self.args.spec_id:
            return str(self.args.spec_id)
        spec_ids = [
            str(document["id"])
            for _, document in documents
            if document.get("kind") == "cad_spec" and isinstance(document.get("id"), str)
        ]
        if len(spec_ids) == 1:
            return spec_ids[0]
        self.error("<args>", "--spec-id is required when the package does not contain exactly one cad_spec")
        return None

    def resolve_layout_interface_refs(self, documents: list[tuple[Path, dict[str, Any]]]) -> list[str] | None:
        if not documents:
            return []
        layout_contracts = [document for _, document in documents if document.get("kind") == "layout_contract"]
        if not layout_contracts:
            return []
        matches: list[dict[str, Any]] = []
        for layout in layout_contracts:
            for part in layout.get("parts", []):
                if isinstance(part, dict) and part.get("part_id") == self.args.part_id:
                    matches.append(part)
        if not matches:
            self.error(self.package or "<package>", f"part_id {self.args.part_id!r} was not found in layout_contract parts")
            return None
        refs: list[str] = []
        for part in matches:
            for ref in part.get("interface_signature_refs", []):
                refs.append(str(ref))
        return sorted(set(refs))

    def build_evidence_sources(self) -> list[dict[str, Any]]:
        observed_at = str(self.args.observed_at)
        sources: list[dict[str, Any]] = []
        for locator in self.args.step_parts_url or []:
            artifact_kind = infer_url_artifact_kind(locator, default="catalog_page")
            trusted_for = ["geometry_reference"] if artifact_kind in {"step", "stp"} else ["source_identity", "review_only"]
            sources.append(
                evidence_source(
                    "step_parts",
                    locator,
                    artifact_kind,
                    trusted_for,
                    "provided_url_not_fetched",
                    observed_at,
                    "step.parts evidence recorded from user-provided locator.",
                )
            )
        for locator in self.args.step_source_url or []:
            artifact_kind = infer_url_artifact_kind(locator, default="step")
            sources.append(
                evidence_source(
                    step_source_type(locator),
                    locator,
                    artifact_kind,
                    ["geometry_reference"],
                    "provided_url_not_fetched",
                    observed_at,
                    "STEP/STP source URL recorded; not downloaded by this tool.",
                )
            )
        for locator in self.args.manufacturer_url or []:
            sources.append(
                evidence_source(
                    "manufacturer",
                    locator,
                    "catalog_page",
                    ["source_identity", "review_only"],
                    "provided_url_not_fetched",
                    observed_at,
                    "Manufacturer product URL recorded as source identity evidence.",
                )
            )
        for locator in self.args.manufacturer_step_url or []:
            artifact_kind = infer_url_artifact_kind(locator, default="step")
            sources.append(
                evidence_source(
                    "manufacturer",
                    locator,
                    artifact_kind,
                    ["source_identity", "geometry_reference"],
                    "provided_url_not_fetched",
                    observed_at,
                    "Manufacturer STEP/STP URL recorded; not downloaded by this tool.",
                )
            )
        for locator in self.args.datasheet_url or []:
            sources.append(
                evidence_source(
                    "datasheet",
                    locator,
                    "datasheet",
                    ["source_identity", "critical_dimensions"],
                    "provided_url_not_fetched",
                    observed_at,
                    "Datasheet URL recorded as identity and dimension reference evidence.",
                )
            )
        for locator in self.args.user_file or []:
            artifact_kind = infer_path_artifact_kind(locator)
            trusted_for = ["geometry_reference"] if artifact_kind in {"step", "stp"} else ["review_only"]
            sources.append(
                evidence_source(
                    "user_provided",
                    locator,
                    artifact_kind,
                    trusted_for,
                    "provided_file_not_inspected",
                    observed_at,
                    "User-provided file path recorded; file content was not inspected by this tool.",
                )
            )
        return sources

    def build_document(
        self,
        spec_id: str,
        interface_refs: list[str],
        evidence_sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        required_before_final = list(DEFAULT_REQUIRED_BEFORE_FINAL)
        required_before_final.extend(self.args.required_before_final or [])
        if self.args.part_role in {"standard_part", "catalog_part", "supplier_part"} and self.args.lock_status == "proxy_only":
            required_before_final.append(PROXY_SOURCE_LOCK_REQUIREMENT)

        claims_not_made = list(DEFAULT_CLAIMS_NOT_MADE)
        claims_not_made.extend(self.args.claim_not_made or [])

        claims_made = sorted(resolve_claims_made(evidence_sources))
        identity_basis = resolve_identity_basis(self.args, evidence_sources)
        product_url = self.args.product_url or first_url(
            list(self.args.manufacturer_url or [])
            + list(self.args.step_parts_url or [])
            + list(self.args.manufacturer_step_url or [])
            + list(self.args.step_source_url or [])
        )

        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "source_lock_evidence",
            "id": sanitize_id(f"{spec_id}.{self.args.part_id}.source_lock"),
            "part_id": self.args.part_id,
            "part_role": self.args.part_role,
            "lock_status": self.args.lock_status,
            "source_identity": {
                "display_name": self.args.name,
                "manufacturer_name": self.args.manufacturer_name or "",
                "model": self.args.model or "",
                "product_url": product_url or "",
                "identity_basis": identity_basis,
            },
            "evidence_sources": evidence_sources,
            "interface_signature_refs": interface_refs,
            "interface_signature_role": "layout_reference_only",
            "claims_made": claims_made,
            "required_before_final": dedupe(required_before_final),
            "claims_not_made": dedupe(claims_not_made),
            "extensions": {
                "generator": "tools/generate_source_lock_evidence.py",
                "package": str(self.package) if self.package is not None else "",
            },
        }


def evidence_source(
    source_type: str,
    locator: str,
    artifact_kind: str,
    trusted_for: list[str],
    retrieval_status: str,
    observed_at: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "artifact_kind": artifact_kind,
        "locator": locator,
        "notes": notes,
        "observed_at": observed_at,
        "retrieval_status": retrieval_status,
        "source_type": source_type,
        "trusted_for": trusted_for,
    }


def infer_url_artifact_kind(locator: str, default: str) -> str:
    suffix = Path(urlparse(locator).path).suffix.lower()
    if suffix == ".step":
        return "step"
    if suffix == ".stp":
        return "stp"
    if suffix == ".pdf":
        return "datasheet"
    return default


def infer_path_artifact_kind(locator: str) -> str:
    suffix = Path(locator).suffix.lower()
    if suffix == ".step":
        return "step"
    if suffix == ".stp":
        return "stp"
    if suffix == ".pdf":
        return "datasheet"
    if suffix in {".json", ".txt", ".md"}:
        return "metadata"
    return "project_file"


def step_source_type(locator: str) -> str:
    host = urlparse(locator).netloc.lower()
    return "step_parts" if host in {"step.parts", "www.step.parts"} else "other"


def resolve_claims_made(evidence_sources: list[dict[str, Any]]) -> set[str]:
    claims: set[str] = set()
    for source in evidence_sources:
        trusted_for = set(source.get("trusted_for", []))
        if "source_identity" in trusted_for or "procurement_identity" in trusted_for:
            claims.add("source_identity")
        if "geometry_reference" in trusted_for:
            claims.add("geometry_reference_url")
        if "critical_dimensions" in trusted_for:
            claims.add("critical_dimensions_reference")
        if "review_only" in trusted_for:
            claims.add("review_reference")
    return claims


def resolve_identity_basis(args: argparse.Namespace, evidence_sources: list[dict[str, Any]]) -> str:
    if args.identity_basis:
        return str(args.identity_basis)
    source_types = {str(source.get("source_type")) for source in evidence_sources}
    if "step_parts" in source_types:
        return "step_parts"
    if "manufacturer" in source_types:
        return "manufacturer_url"
    if "datasheet" in source_types:
        return "datasheet"
    if "project_file" in source_types:
        return "project_file"
    if "user_provided" in source_types:
        return "user_provided"
    return "unresolved"


def first_url(values: list[str]) -> str:
    for value in values:
        if value:
            return value
    return ""


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value)
        if text not in seen:
            seen.add(text)
            result.append(text)
    return result


def sanitize_id(value: str) -> str:
    lowered = value.lower()
    sanitized = re.sub(r"[^a-z0-9_.-]+", "_", lowered).strip("_.-")
    return sanitized or "source_lock"


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Zen CAD source-lock evidence artifact from explicit source locators.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, help="Optional contract package used to resolve spec_id and layout interface refs.")
    parser.add_argument("--spec-id", help="Spec id when no package cad_spec is available.")
    parser.add_argument("--part-id", required=True, help="Part id from the layout contract or final sourcing target.")
    parser.add_argument(
        "--part-role",
        choices=["standard_part", "catalog_part", "supplier_part", "generated_custom_part", "proxy"],
        default="catalog_part",
    )
    parser.add_argument("--lock-status", choices=["source_locked", "unresolved", "proxy_only"], default="source_locked")
    parser.add_argument("--name", required=True, help="Human-readable source identity name.")
    parser.add_argument("--manufacturer-name", default="", help="Manufacturer or maker name when provided by evidence.")
    parser.add_argument("--model", default="", help="Model or part identifier when provided by evidence.")
    parser.add_argument("--product-url", default="", help="Canonical product/source URL when known.")
    parser.add_argument(
        "--identity-basis",
        choices=["step_parts", "manufacturer_url", "datasheet", "project_file", "user_provided", "unresolved"],
        help="Override inferred source identity basis.",
    )
    parser.add_argument("--interface-signature-ref", action="append", default=[], help="Layout-only interface signature ref. Repeatable.")
    parser.add_argument("--step-parts-url", action="append", default=[], help="step.parts part page URL. Repeatable.")
    parser.add_argument("--step-source-url", action="append", default=[], help="STEP/STP source URL. Repeatable.")
    parser.add_argument("--manufacturer-url", action="append", default=[], help="Manufacturer product page URL. Repeatable.")
    parser.add_argument("--manufacturer-step-url", action="append", default=[], help="Manufacturer STEP/STP URL. Repeatable.")
    parser.add_argument("--datasheet-url", action="append", default=[], help="Datasheet URL. Repeatable.")
    parser.add_argument("--user-file", action="append", default=[], help="User-provided evidence file path. Repeatable.")
    parser.add_argument("--required-before-final", action="append", default=[], help="Additional final-stage requirement. Repeatable.")
    parser.add_argument("--claim-not-made", action="append", default=[], help="Additional non-claim statement. Repeatable.")
    parser.add_argument("--observed-at", default=date.today().isoformat(), help="Date associated with recorded locators.")
    parser.add_argument("--out", type=Path, required=True, help="Output source_lock_evidence JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    generator = SourceLockEvidenceGenerator(args.repo_root, args.package, args.out, args)
    result = generator.generate()
    if generator.issues:
        for issue in generator.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("source lock evidence generation failed", file=sys.stderr)
        return 1
    print(f"Source lock evidence: {result.evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
