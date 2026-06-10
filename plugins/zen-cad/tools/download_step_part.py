#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"
DEFAULT_API_ORIGIN = "https://api.step.parts"
DEFAULT_SITE_ORIGIN = "https://www.step.parts"


@dataclass
class StepPartResult:
    record: dict[str, Any]
    step_path: Path | None = None
    sha256: str | None = None


class StepPartDownloader:
    def __init__(self, repo_root: Path, args: argparse.Namespace) -> None:
        self.repo_root = repo_root
        self.args = args
        self.issues: list[Issue] = []

    def error(self, path: Path | str, message: str) -> None:
        self.issues.append(Issue(str(path), message))

    def run(self) -> dict[str, Any] | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        if self.args.package is not None:
            validator.validate_package(self.args.package)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        records = self.resolve_records()
        if records is None:
            return None
        if not records:
            return self.result_payload([])

        selected = records if self.args.all else records[:1]
        results: list[StepPartResult] = []
        for record in selected:
            result = StepPartResult(record=record)
            if self.args.download:
                result.step_path, result.sha256 = self.download_record(record)
                if self.issues:
                    return None
            results.append(result)

        if self.args.source_lock_out:
            if len(results) != 1:
                self.error("--source-lock-out", "source-lock generation requires exactly one selected step.parts record")
                return None
            if results[0].step_path is None or results[0].sha256 is None:
                self.error("--source-lock-out", "source-lock generation requires --download so the STEP checksum can be recorded")
                return None
            document = self.build_source_lock(results[0])
            self.args.source_lock_out.parent.mkdir(parents=True, exist_ok=True)
            write_json(self.args.source_lock_out, document)
            output_validator = ContractValidator(self.repo_root)
            output_validator.validate_package(self.args.source_lock_out)
            if output_validator.issues:
                self.issues.extend(output_validator.issues)
                return None

        return self.result_payload(results)

    def resolve_records(self) -> list[dict[str, Any]] | None:
        if self.args.id:
            record = self.get_part(self.args.id)
            return [record] if isinstance(record, dict) else None
        if not self.args.query:
            self.error("<args>", "provide a query or --id")
            return None
        payload = self.search_parts(self.args.query)
        if not isinstance(payload, dict):
            return None
        items = payload.get("items", [])
        if not isinstance(items, list):
            self.error("<api>", "step.parts search response missing items list")
            return None
        return [item for item in items if isinstance(item, dict)]

    def search_parts(self, query: str) -> dict[str, Any] | None:
        params: list[tuple[str, str]] = [("q", query), ("pageSize", str(self.args.limit))]
        for name in ["tag", "category", "family", "standard"]:
            for value in getattr(self.args, name) or []:
                params.append((name, value))
        url = f"{self.args.origin.rstrip('/')}/v1/parts?{urlencode(params)}"
        return self.fetch_json(url)

    def get_part(self, part_id: str) -> dict[str, Any] | None:
        return self.fetch_json(f"{self.args.origin.rstrip('/')}/v1/parts/{part_id}")

    def fetch_json(self, url: str) -> dict[str, Any] | None:
        data = self.fetch_bytes(url)
        if data is None:
            return None
        try:
            loaded = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self.error(url, f"invalid JSON from step.parts API: {exc}")
            return None
        return loaded if isinstance(loaded, dict) else None

    def fetch_bytes(self, url: str) -> bytes | None:
        request = Request(url, headers={"User-Agent": "zen-cad-step-parts/1.0"})
        try:
            with urlopen(request, timeout=self.args.timeout) as response:
                return response.read()
        except Exception as first_exc:
            # macOS framework Python often lacks a configured CA bundle. Keep
            # urllib as the primary path, but fall back to system curl with
            # normal certificate verification instead of disabling TLS checks.
            curl = subprocess.run(
                ["curl", "-fsSL", "--max-time", str(int(self.args.timeout)), url],
                text=False,
                capture_output=True,
                check=False,
            )
            if curl.returncode == 0:
                return curl.stdout
            stderr = curl.stderr.decode("utf-8", errors="replace").strip()
            self.error(url, f"fetch failed: {type(first_exc).__name__}: {first_exc}; curl: {stderr}")
            return None

    def download_record(self, record: dict[str, Any]) -> tuple[Path, str] | tuple[None, None]:
        step_url = str(record.get("stepUrl", ""))
        if not step_url:
            self.error(record.get("id", "<record>"), "selected step.parts record has no stepUrl")
            return None, None
        data = self.fetch_bytes(step_url)
        if data is None:
            return None, None
        digest = hashlib.sha256(data).hexdigest()
        expected = str(record.get("sha256", ""))
        if expected and digest.lower() != expected.lower():
            self.error(step_url, f"sha256 mismatch: expected {expected}, got {digest}")
            return None, None
        out_dir = self.args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = safe_filename(str(record.get("id") or Path(step_url).stem)) + ".step"
        target = out_dir / filename
        if target.exists() and not self.args.overwrite:
            existing_digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if existing_digest == digest:
                return target, digest
            self.error(target, "file already exists with a different sha256; use --overwrite to replace it")
            return None, None
        target.write_bytes(data)
        return target, digest

    def build_source_lock(self, result: StepPartResult) -> dict[str, Any]:
        record = result.record
        package = self.args.package
        spec_id = self.resolve_spec_id()
        local_locator = relative_locator(result.step_path, package, self.repo_root) if result.step_path else ""
        page_url = str(record.get("pageUrl") or f"{DEFAULT_SITE_ORIGIN}/parts/{record.get('id', '')}")
        step_url = str(record.get("stepUrl", ""))
        sha256 = str(result.sha256 or record.get("sha256", ""))
        interface_refs = list(self.args.interface_signature_ref or [])
        if not interface_refs and package is not None:
            interface_refs = self.resolve_interface_refs(package, str(self.args.part_id))

        required_before_final = [
            "Import the locked source geometry in the downstream CAD harness.",
            "Run geometry checks for required datums, axes, interfaces, and clearances.",
            "Stop if source geometry changes an approved locked layout fact.",
            *list(self.args.required_before_final or []),
        ]
        claims_not_made = [
            "No rating, load capacity, torque capacity, or safety factor is claimed.",
            "No certification, compliance, price, inventory, or availability is claimed.",
            "No generated STEP geometry is certified by this evidence artifact alone.",
            *list(self.args.claim_not_made or []),
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "source_lock_evidence",
            "id": sanitize_id(f"{spec_id}.{self.args.part_id}.source_lock"),
            "part_id": self.args.part_id,
            "part_role": self.args.part_role,
            "lock_status": "source_locked",
            "source_identity": {
                "display_name": self.args.name or str(record.get("name") or record.get("id")),
                "manufacturer_name": self.args.manufacturer_name or "",
                "model": self.args.model or str(record.get("id", "")),
                "product_url": page_url,
                "identity_basis": "step_parts",
            },
            "evidence_sources": [
                evidence_source("step_parts", page_url, "catalog_page", ["source_identity", "review_only"], "inspected_elsewhere", self.args.observed_at, "Selected step.parts catalog record."),
                evidence_source("step_parts", str(record.get("apiUrl") or f"{self.args.origin.rstrip('/')}/v1/parts/{record.get('id', '')}"), "metadata", ["source_identity", "review_only"], "inspected_elsewhere", self.args.observed_at, "Selected api.step.parts record."),
                evidence_source("step_parts", step_url, "step", ["geometry_reference"], "checksum_recorded", self.args.observed_at, "Downloaded from record.stepUrl and verified against record sha256.", sha256),
                evidence_source("project_file", local_locator, "step", ["geometry_reference"], "checksum_recorded", self.args.observed_at, "Local checksum-verified STEP copy; preferred import locator.", sha256),
            ],
            "interface_signature_refs": sorted(set(interface_refs)),
            "interface_signature_role": "layout_reference_only",
            "claims_made": ["geometry_reference_url", "review_reference", "source_identity"],
            "required_before_final": dedupe(required_before_final),
            "claims_not_made": dedupe(claims_not_made),
            "extensions": {
                "generator": "tools/download_step_part.py",
                "step_parts_record": slim_record(record),
                "downloaded_step": str(result.step_path) if result.step_path else "",
                "sha256_verified": bool(sha256),
            },
        }

    def resolve_spec_id(self) -> str:
        if self.args.spec_id:
            return str(self.args.spec_id)
        if self.args.package is None:
            return "zen_cad"
        paths = [self.args.package] if self.args.package.is_file() else sorted(self.args.package.rglob("*.json"))
        for path in paths:
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(document, dict) and document.get("kind") == "cad_spec" and isinstance(document.get("id"), str):
                return document["id"]
        return "zen_cad"

    def resolve_interface_refs(self, package: Path, part_id: str) -> list[str]:
        paths = [package] if package.is_file() else sorted(package.rglob("*.json"))
        refs: list[str] = []
        for path in paths:
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(document, dict) or document.get("kind") != "layout_contract":
                continue
            for part in document.get("parts", []):
                if isinstance(part, dict) and part.get("part_id") == part_id:
                    refs.extend(str(ref) for ref in part.get("interface_signature_refs", []) if isinstance(ref, str))
        return refs

    def result_payload(self, results: list[StepPartResult] | list[dict[str, Any]]) -> dict[str, Any]:
        if results and isinstance(results[0], dict):
            items = [slim_record(item) for item in results]  # type: ignore[arg-type]
        else:
            items = [
                {
                    **slim_record(result.record),
                    "saved_step": str(result.step_path) if result.step_path else "",
                    "sha256": result.sha256 or str(result.record.get("sha256", "")),
                }
                for result in results  # type: ignore[union-attr]
            ]
        payload = {
            "query": self.args.query or "",
            "id": self.args.id or "",
            "count": len(items),
            "items": items,
        }
        if self.args.source_lock_out:
            payload["source_lock"] = str(self.args.source_lock_out)
        return payload


def evidence_source(
    source_type: str,
    locator: str,
    artifact_kind: str,
    trusted_for: list[str],
    retrieval_status: str,
    observed_at: str,
    notes: str,
    sha256: str = "",
) -> dict[str, Any]:
    source: dict[str, Any] = {
        "artifact_kind": artifact_kind,
        "locator": locator,
        "notes": notes,
        "observed_at": observed_at,
        "retrieval_status": retrieval_status,
        "source_type": source_type,
        "trusted_for": trusted_for,
    }
    if sha256:
        source["sha256"] = sha256
    return source


def slim_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(record.get("id", "")),
        "name": str(record.get("name", "")),
        "category": str(record.get("category", "")),
        "family": str(record.get("family", "")),
        "standard": record.get("standard", {}),
        "attributes": record.get("attributes", {}),
        "pageUrl": str(record.get("pageUrl", "")),
        "apiUrl": str(record.get("apiUrl", "")),
        "stepUrl": str(record.get("stepUrl", "")),
        "sha256": str(record.get("sha256", "")),
        "byteSize": record.get("byteSize", 0),
    }


def relative_locator(path: Path | None, package: Path | None, repo_root: Path) -> str:
    if path is None:
        return ""
    resolved = path.resolve()
    bases = []
    if package is not None:
        bases.append(package if package.is_dir() else package.parent)
    bases.append(repo_root)
    for base in bases:
        try:
            return str(resolved.relative_to(base.resolve()))
        except ValueError:
            continue
    return str(resolved)


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.-") or "step_part"


def sanitize_id(value: str) -> str:
    return re.sub(r"[^a-z0-9_.-]+", "_", value.lower()).strip("_.-") or "source_lock"


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search, download, and source-lock STEP parts from api.step.parts.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("query", nargs="?", help="Fuzzy step.parts search query.")
    parser.add_argument("--id", help="Exact step.parts part id.")
    parser.add_argument("--origin", default=DEFAULT_API_ORIGIN, help="step.parts API origin.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum search results to request.")
    parser.add_argument("--tag", action="append", default=[], help="Repeatable tag facet.")
    parser.add_argument("--category", action="append", default=[], help="Repeatable category facet.")
    parser.add_argument("--family", action="append", default=[], help="Repeatable family facet.")
    parser.add_argument("--standard", action="append", default=[], help="Repeatable standard facet.")
    parser.add_argument("--download", action="store_true", help="Download selected STEP file(s).")
    parser.add_argument("--all", action="store_true", help="With --download, download every result on the returned page.")
    parser.add_argument("--out-dir", type=Path, default=Path("sourced_parts/step_parts"), help="Directory for downloaded STEP files.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing local STEP file.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds.")
    parser.add_argument("--package", type=Path, help="Contract package used for validation/spec/interface lookup.")
    parser.add_argument("--spec-id", help="Spec id when no package cad_spec is available.")
    parser.add_argument("--part-id", help="Zen CAD layout part id for source-lock evidence.")
    parser.add_argument("--part-role", choices=["standard_part", "catalog_part", "supplier_part", "generated_custom_part", "proxy"], default="standard_part")
    parser.add_argument("--name", default="", help="Human-readable source identity name. Defaults to step.parts record name.")
    parser.add_argument("--manufacturer-name", default="", help="Manufacturer name if known.")
    parser.add_argument("--model", default="", help="Model/part id override. Defaults to step.parts id.")
    parser.add_argument("--interface-signature-ref", action="append", default=[], help="Layout-only interface signature ref. Repeatable.")
    parser.add_argument("--required-before-final", action="append", default=[], help="Additional final-stage requirement. Repeatable.")
    parser.add_argument("--claim-not-made", action="append", default=[], help="Additional non-claim statement. Repeatable.")
    parser.add_argument("--observed-at", default=date.today().isoformat(), help="Date associated with the source-lock evidence.")
    parser.add_argument("--source-lock-out", type=Path, help="Optional source_lock_evidence JSON output path.")
    args = parser.parse_args(argv)
    if args.source_lock_out and not args.part_id:
        parser.error("--source-lock-out requires --part-id")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    downloader = StepPartDownloader(args.repo_root, args)
    result = downloader.run()
    if downloader.issues:
        for issue in downloader.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("step.parts operation failed", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
