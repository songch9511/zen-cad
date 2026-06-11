#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCHEMA_VERSION = "0.8.0"

SCHEMA_FILES = {
    "cad_spec.schema.json": "cad_spec",
    "layout_contract.schema.json": "layout_contract",
    "interface_signature.schema.json": "interface_signature",
    "inspection_report.schema.json": "inspection_report",
    "handoff_packet.schema.json": "handoff_packet",
    "layout_proxy_scene.schema.json": "layout_proxy_scene",
    "cad_source_manifest.schema.json": "cad_source_manifest",
    "proceed_gate_package.schema.json": "proceed_gate_package",
    "proceed_approval.schema.json": "proceed_approval",
    "pipeline_run.schema.json": "pipeline_run",
    "source_lock_evidence.schema.json": "source_lock_evidence",
    "review_bundle.schema.json": "review_bundle",
    "interface_frame.schema.json": "interface_frame",
    "replacement_plan.schema.json": "replacement_plan",
    "detail_shape_plan.schema.json": "detail_shape_plan",
}

COMMON_SCHEMA_REQUIRED = {"schema_version", "kind", "extensions"}

INTERFACE_REQUIRED = {
    "schema_version",
    "kind",
    "id",
    "title",
    "units",
    "family",
    "quality_label",
    "trusted_for_layout",
    "source",
    "primary_axes",
    "mounting_datums",
    "critical_dimensions",
    "envelope",
    "validation_targets",
    "proxy_may_simplify",
    "must_confirm_before_final",
    "extensions",
}

FORBIDDEN_REGISTRY_KEYS = {
    "manufacturer",
    "supplier",
    "sku",
    "price",
    "availability",
    "bom_quantity",
    "step_file",
    "cad_file",
    "load_rating",
    "torque_rating",
    "material",
    "certification",
}

FORBIDDEN_SOURCE_LOCK_KEYS = {
    "sku",
    "price",
    "availability",
    "bom_quantity",
    "load_rating",
    "torque_rating",
    "material",
    "certification",
}


@dataclass
class Issue:
    path: str
    message: str


class ContractValidator:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
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

    def validate_repo(self) -> list[Issue]:
        self.validate_schemas()
        self.validate_registry()
        return self.issues

    def validate_schemas(self) -> None:
        schema_root = self.repo_root / "schemas"
        for filename, kind in SCHEMA_FILES.items():
            path = schema_root / filename
            schema = self.load_json(path)
            if not isinstance(schema, dict):
                continue
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                self.error(path, "schema must use JSON Schema Draft 2020-12")
            if schema.get("type") != "object":
                self.error(path, "top-level schema type must be object")
            if schema.get("additionalProperties") is not False:
                self.error(path, "stable schema must set additionalProperties to false")
            required = set(schema.get("required", []))
            missing = sorted(COMMON_SCHEMA_REQUIRED - required)
            if missing:
                self.error(path, f"missing common required fields: {', '.join(missing)}")
            properties = schema.get("properties", {})
            if properties.get("schema_version", {}).get("const") != SCHEMA_VERSION:
                self.error(path, f"schema_version const must be {SCHEMA_VERSION}")
            if properties.get("kind", {}).get("const") != kind:
                self.error(path, f"kind const must be {kind}")

    def validate_registry(self) -> None:
        registry_root = self.repo_root / "registry" / "interfaces"
        index_path = registry_root / "index.json"
        index = self.load_json(index_path)
        if not isinstance(index, dict):
            return
        if index.get("schema_version") != SCHEMA_VERSION:
            self.error(index_path, f"schema_version must be {SCHEMA_VERSION}")
        if index.get("kind") != "interface_registry_index":
            self.error(index_path, "kind must be interface_registry_index")
        entries = index.get("entries")
        if not isinstance(entries, list) or not entries:
            self.error(index_path, "entries must be a non-empty list")
            return
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, str):
                self.error(index_path, "entries must contain only string paths")
                continue
            if entry in seen:
                self.error(index_path, f"duplicate registry entry: {entry}")
            seen.add(entry)
            if entry.startswith("/") or ".." in Path(entry).parts:
                self.error(index_path, f"registry entry must be relative and contained: {entry}")
                continue
            record_path = registry_root / entry
            record = self.load_json(record_path)
            if isinstance(record, dict):
                self.validate_interface_signature(record_path, record)

    def validate_interface_signature(self, path: Path, record: dict[str, Any]) -> None:
        missing = sorted(INTERFACE_REQUIRED - set(record))
        if missing:
            self.error(path, f"missing interface fields: {', '.join(missing)}")
            return
        if record.get("schema_version") != SCHEMA_VERSION:
            self.error(path, f"schema_version must be {SCHEMA_VERSION}")
        if record.get("kind") != "interface_signature":
            self.error(path, "kind must be interface_signature")
        if record.get("units") != "mm":
            self.error(path, "units must be mm")
        if not record.get("trusted_for_layout"):
            self.error(path, "built-in registry records must be trusted_for_layout")
        forbidden = sorted(FORBIDDEN_REGISTRY_KEYS & walk_keys(record))
        if forbidden:
            self.error(path, f"registry record contains procurement or final-claim keys: {', '.join(forbidden)}")
        for field in [
            "primary_axes",
            "mounting_datums",
            "critical_dimensions",
            "validation_targets",
            "proxy_may_simplify",
            "must_confirm_before_final",
        ]:
            if not isinstance(record.get(field), list) or not record[field]:
                self.error(path, f"{field} must be a non-empty list")
        for dimension in record.get("critical_dimensions", []):
            if not isinstance(dimension, dict):
                self.error(path, "critical_dimensions entries must be objects")
                continue
            for field in ["name", "value", "units", "status"]:
                if field not in dimension:
                    self.error(path, f"critical dimension missing {field}")

    def validate_package(self, package: Path) -> list[Issue]:
        documents = self.load_package_documents(package)
        if documents is None:
            return self.issues

        by_kind: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
        seen_documents: dict[str, dict[str, Any]] = {}
        for path, document in documents:
            if not isinstance(document, dict):
                self.error(path, "contract document must be a JSON object")
                continue
            kind = document.get("kind")
            doc_id = document.get("id")
            if not isinstance(kind, str):
                self.error(path, "document must have string kind")
                continue
            if not isinstance(doc_id, str) or not doc_id:
                self.error(path, "document must have non-empty string id")
                continue
            if document.get("schema_version") != SCHEMA_VERSION:
                self.error(path, f"schema_version must be {SCHEMA_VERSION}")
            extensions = document.get("extensions")
            if not isinstance(extensions, dict):
                self.error(path, "document must include object extensions")
            if doc_id in seen_documents:
                if document != seen_documents[doc_id]:
                    self.error(path, f"duplicate document id with different content: {doc_id}")
            else:
                seen_documents[doc_id] = document
            by_kind.setdefault(kind, []).append((path, document))

        for path, document in by_kind.get("cad_spec", []):
            self.validate_cad_spec_document(path, document)
        for path, document in by_kind.get("handoff_packet", []):
            self.validate_handoff_document(path, document)
        for path, document in by_kind.get("inspection_report", []):
            self.validate_inspection_document(path, document)
        for path, document in by_kind.get("interface_signature", []):
            self.validate_interface_signature(path, document)
        for path, document in by_kind.get("layout_proxy_scene", []):
            self.validate_layout_proxy_scene_document(path, document)
        for path, document in by_kind.get("cad_source_manifest", []):
            self.validate_cad_source_manifest_document(path, document)
        for path, document in by_kind.get("proceed_gate_package", []):
            self.validate_proceed_gate_package_document(path, document)
        for path, document in by_kind.get("proceed_approval", []):
            self.validate_proceed_approval_document(path, document)
        for path, document in by_kind.get("pipeline_run", []):
            self.validate_pipeline_run_document(path, document)
        for path, document in by_kind.get("source_lock_evidence", []):
            self.validate_source_lock_evidence_document(path, document)
        for path, document in by_kind.get("review_bundle", []):
            self.validate_review_bundle_document(path, document)
        for path, document in by_kind.get("interface_frame", []):
            self.validate_interface_frame_document(path, document)
        for path, document in by_kind.get("replacement_plan", []):
            self.validate_replacement_plan_document(path, document)
        for path, document in by_kind.get("detail_shape_plan", []):
            self.validate_detail_shape_plan_document(path, document)

        return self.issues

    def load_package_documents(self, package: Path) -> list[tuple[Path, Any]] | None:
        if package.is_file():
            return [(package, self.load_json(package))]
        if not package.is_dir():
            self.error(package, "package path must be a JSON file or directory")
            return None
        paths = sorted(path for path in package.rglob("*.json") if path.is_file())
        if not paths:
            self.error(package, "package directory contains no JSON documents")
            return None
        return [(path, self.load_json(path)) for path in paths]

    def validate_cad_spec_document(self, path: Path, document: dict[str, Any]) -> None:
        required = {
            "parameter_contract",
            "artifact_targets",
            "locked_layout_facts",
            "inspection_plan",
            "repair_loop",
            "proceed_gate",
            "downstream_handoff",
        }
        missing = sorted(required - set(document))
        if missing:
            self.error(path, f"cad_spec missing required fields: {', '.join(missing)}")
        locked_facts = document.get("locked_layout_facts", [])
        if not isinstance(locked_facts, list) or not locked_facts:
            self.error(path, "cad_spec locked_layout_facts must be a non-empty list")
        inspection_plan = document.get("inspection_plan", [])
        if not isinstance(inspection_plan, list) or not inspection_plan:
            self.error(path, "cad_spec inspection_plan must be a non-empty list")
        check_ids = {check.get("check_id") for check in inspection_plan if isinstance(check, dict)}
        for fact in locked_facts if isinstance(locked_facts, list) else []:
            if not isinstance(fact, dict):
                self.error(path, "locked layout facts must be objects")
                continue
            if fact.get("must_preserve") is not True:
                self.error(path, f"locked fact {fact.get('fact_id', '<unknown>')} must set must_preserve true")
            if not any(fact.get("fact_id") in check.get("locked_fact_refs", []) for check in inspection_plan if isinstance(check, dict)):
                self.error(path, f"locked fact {fact.get('fact_id', '<unknown>')} has no inspection check")
        handoff = document.get("downstream_handoff")
        if isinstance(handoff, dict):
            required_handoff = {"locked_facts", "required_checks", "stop_conditions"}
            missing_handoff = sorted(required_handoff - set(handoff))
            if missing_handoff:
                self.error(path, f"embedded downstream_handoff missing: {', '.join(missing_handoff)}")
            for check_ref in handoff.get("required_checks", []):
                if check_ref not in check_ids:
                    self.error(path, f"handoff required check not declared in inspection_plan: {check_ref}")

    def validate_handoff_document(self, path: Path, document: dict[str, Any]) -> None:
        if not document.get("locked_facts"):
            self.error(path, "handoff_packet must embed locked_facts")
        if not document.get("required_checks"):
            self.error(path, "handoff_packet must include required_checks")
        if not document.get("stop_conditions"):
            self.error(path, "handoff_packet must include stop_conditions")
        stop_text = " ".join(str(item) for item in document.get("stop_conditions", []))
        if "locked" not in stop_text.lower():
            self.error(path, "handoff_packet stop_conditions must mention locked facts")

    def validate_inspection_document(self, path: Path, document: dict[str, Any]) -> None:
        checks = document.get("checks", [])
        if not isinstance(checks, list):
            self.error(path, "inspection_report checks must be a list")
            return
        for check in checks:
            if not isinstance(check, dict):
                self.error(path, "inspection_report check entries must be objects")
                continue
            if check.get("status") == "passed" and not str(check.get("evidence", "")).strip():
                self.error(path, f"passed check {check.get('check_id', '<unknown>')} must include evidence")
        for skipped in document.get("skipped_checks", []):
            if not isinstance(skipped, dict) or not str(skipped.get("reason", "")).strip():
                self.error(path, "skipped checks must include a reason")

    def validate_layout_proxy_scene_document(self, path: Path, document: dict[str, Any]) -> None:
        primitives = document.get("primitives", [])
        if not isinstance(primitives, list) or not primitives:
            self.error(path, "layout_proxy_scene primitives must be a non-empty list")
        for primitive in primitives if isinstance(primitives, list) else []:
            if not isinstance(primitive, dict):
                self.error(path, "layout_proxy_scene primitive entries must be objects")
                continue
            for field in ["id", "part_id", "type", "frame", "dimensions", "derived_from", "fidelity"]:
                if field not in primitive:
                    self.error(path, f"layout_proxy_scene primitive missing {field}")
            if primitive.get("fidelity") != "layout_only":
                self.error(path, "layout_proxy_scene primitives must use layout_only fidelity")
        for skipped in document.get("skipped_checks", []):
            if not isinstance(skipped, dict) or not str(skipped.get("reason", "")).strip():
                self.error(path, "layout_proxy_scene skipped checks must include a reason")

    def validate_cad_source_manifest_document(self, path: Path, document: dict[str, Any]) -> None:
        required = {
            "source_scene_id",
            "target_harness",
            "source_path",
            "expected_primary_artifact",
            "generated_files",
            "primitives",
            "locked_layout_facts",
            "inspection_targets",
            "source_of_truth",
        }
        missing = sorted(required - set(document))
        if missing:
            self.error(path, f"cad_source_manifest missing required fields: {', '.join(missing)}")
        if not document.get("generated_files"):
            self.error(path, "cad_source_manifest generated_files must be non-empty")
        if not document.get("primitives"):
            self.error(path, "cad_source_manifest primitives must be non-empty")
        if document.get("target_harness") not in {"build123d", "cadquery", "freecad", "unknown"}:
            self.error(path, "cad_source_manifest target_harness is not supported")
        sourced_parts = document.get("sourced_parts", [])
        if sourced_parts is not None and not isinstance(sourced_parts, list):
            self.error(path, "cad_source_manifest sourced_parts must be a list")
        for item in sourced_parts if isinstance(sourced_parts, list) else []:
            if not isinstance(item, dict):
                self.error(path, "cad_source_manifest sourced_parts entries must be objects")
                continue
            missing = sorted({"part_id", "source_lock_id", "locator", "artifact_kind", "import_strategy"} - set(item))
            if missing:
                self.error(path, f"cad_source_manifest sourced part missing fields: {', '.join(missing)}")
            if item.get("artifact_kind") not in {"step", "stp"}:
                self.error(path, "cad_source_manifest sourced part artifact_kind must be step or stp")
            if item.get("import_strategy") != "build123d.import_step":
                self.error(path, "cad_source_manifest sourced part import_strategy must be build123d.import_step")
            if item.get("sha256") and not re.fullmatch(r"[a-fA-F0-9]{64}", str(item.get("sha256"))):
                self.error(path, "cad_source_manifest sourced part sha256 must be 64 hex characters")

    def validate_proceed_gate_package_document(self, path: Path, document: dict[str, Any]) -> None:
        if not document.get("decision_options"):
            self.error(path, "proceed_gate_package decision_options must be non-empty")
        if not document.get("artifacts"):
            self.error(path, "proceed_gate_package artifacts must be non-empty")
        if not document.get("reports"):
            self.error(path, "proceed_gate_package reports must be non-empty")
        if not document.get("locked_layout_facts"):
            self.error(path, "proceed_gate_package locked_layout_facts must be non-empty")
        summary = document.get("check_summary", {})
        if not isinstance(summary, dict):
            self.error(path, "proceed_gate_package check_summary must be an object")
            return
        if document.get("status") == "ready_for_user_review" and int(summary.get("failed", 0)) > 0:
            self.error(path, "ready_for_user_review cannot have failed checks")

    def validate_proceed_approval_document(self, path: Path, document: dict[str, Any]) -> None:
        if document.get("decision") not in {"proceed", "detail_upgrade"}:
            self.error(path, "proceed_approval decision must be proceed or detail_upgrade")
        if document.get("approved_next_maturity") != "detail_cad":
            self.error(path, "proceed_approval approved_next_maturity must be detail_cad")
        if not document.get("proceed_gate_id"):
            self.error(path, "proceed_approval must reference proceed_gate_id")
        if not document.get("approver"):
            self.error(path, "proceed_approval approver must be non-empty")
        if not document.get("approved_at"):
            self.error(path, "proceed_approval approved_at must be non-empty")
        if not document.get("locked_layout_facts"):
            self.error(path, "proceed_approval locked_layout_facts must be non-empty")

    def validate_pipeline_run_document(self, path: Path, document: dict[str, Any]) -> None:
        steps = document.get("steps", [])
        if not isinstance(steps, list) or not steps:
            self.error(path, "pipeline_run steps must be a non-empty list")
            return
        for step in steps:
            if not isinstance(step, dict):
                self.error(path, "pipeline_run step entries must be objects")
                continue
            if step.get("status") not in {"passed", "failed", "skipped"}:
                self.error(path, f"pipeline_run step {step.get('step_id', '<unknown>')} has invalid status")
            if "outputs" not in step or "issues" not in step or "note" not in step:
                self.error(path, f"pipeline_run step {step.get('step_id', '<unknown>')} missing outputs, issues, or note")
        status = document.get("status")
        if status == "completed" and not document.get("artifacts", {}).get("detail_handoff"):
            self.error(path, "completed pipeline_run must include detail_handoff artifact")
        if status == "ready_for_user_review" and not document.get("artifacts", {}).get("proceed_gate"):
            self.error(path, "ready_for_user_review pipeline_run must include proceed_gate artifact")

    def validate_source_lock_evidence_document(self, path: Path, document: dict[str, Any]) -> None:
        required = {
            "part_id",
            "part_role",
            "lock_status",
            "source_identity",
            "evidence_sources",
            "interface_signature_refs",
            "interface_signature_role",
            "claims_made",
            "required_before_final",
            "claims_not_made",
        }
        missing = sorted(required - set(document))
        if missing:
            self.error(path, f"source_lock_evidence missing required fields: {', '.join(missing)}")
        status = document.get("lock_status")
        sources = document.get("evidence_sources", [])
        if document.get("part_role") not in {"standard_part", "catalog_part", "supplier_part", "generated_custom_part", "proxy"}:
            self.error(path, "source_lock_evidence part_role is invalid")
        if status not in {"source_locked", "unresolved", "proxy_only"}:
            self.error(path, "source_lock_evidence lock_status is invalid")
        if document.get("interface_signature_role") != "layout_reference_only":
            self.error(path, "source_lock_evidence must mark interface signatures as layout_reference_only")
        identity = document.get("source_identity")
        if not isinstance(identity, dict):
            self.error(path, "source_lock_evidence source_identity must be an object")
        elif status == "source_locked" and identity.get("identity_basis") == "unresolved":
            self.error(path, "source_locked evidence must use a resolved source_identity identity_basis")
        if not isinstance(sources, list) or not sources:
            self.error(path, "source_lock_evidence evidence_sources must be non-empty")
            return
        for source in sources:
            self.validate_source_lock_evidence_source(path, source)
        if status == "source_locked":
            trusted = {
                item
                for source in sources
                if isinstance(source, dict)
                for item in source.get("trusted_for", [])
            }
            if "geometry_reference" not in trusted and "source_identity" not in trusted and "procurement_identity" not in trusted:
                self.error(path, "source_locked evidence must be trusted for geometry_reference or source_identity")
            if trusted <= {"layout", "review_only"}:
                self.error(path, "source_locked evidence cannot rely only on layout or review evidence")
        if document.get("part_role") in {"standard_part", "catalog_part", "supplier_part"} and status == "proxy_only":
            required = "Replace proxy with step.parts, manufacturer, datasheet, or user-provided source before final."
            if required not in document.get("required_before_final", []):
                self.error(path, "proxy standard/catalog parts must state the final source-lock requirement")
        forbidden = sorted(FORBIDDEN_SOURCE_LOCK_KEYS & walk_keys(document))
        if forbidden:
            self.error(path, f"source_lock_evidence contains final-claim keys: {', '.join(forbidden)}")
        claims_made = document.get("claims_made", [])
        allowed_claims = {"source_identity", "geometry_reference_url", "critical_dimensions_reference", "review_reference"}
        if not isinstance(claims_made, list):
            self.error(path, "source_lock_evidence claims_made must be a list")
        else:
            unsupported = sorted({str(item) for item in claims_made} - allowed_claims)
            if unsupported:
                self.error(path, f"source_lock_evidence claims_made contains unsupported claims: {', '.join(unsupported)}")
        claims_text = " ".join(str(item).lower() for item in document.get("claims_not_made", []))
        for required_phrase in ["rating", "certification"]:
            if required_phrase not in claims_text:
                self.error(path, f"source_lock_evidence claims_not_made must mention {required_phrase}")

    def validate_source_lock_evidence_source(self, path: Path, source: Any) -> None:
        if not isinstance(source, dict):
            self.error(path, "source_lock_evidence evidence_sources entries must be objects")
            return
        required = {"source_type", "locator", "artifact_kind", "trusted_for", "retrieval_status"}
        missing = sorted(required - set(source))
        if missing:
            self.error(path, f"source_lock_evidence evidence source missing required fields: {', '.join(missing)}")
        source_type = source.get("source_type")
        locator = str(source.get("locator", "")).strip()
        artifact_kind = source.get("artifact_kind")
        trusted_for = source.get("trusted_for", [])
        if source_type not in {"step_parts", "manufacturer", "datasheet", "project_file", "user_provided", "other"}:
            self.error(path, "source_lock_evidence evidence source_type is invalid")
        if artifact_kind not in {"step", "stp", "datasheet", "catalog_page", "project_file", "metadata", "unknown"}:
            self.error(path, "source_lock_evidence evidence artifact_kind is invalid")
        if source.get("retrieval_status") not in {"provided_url_not_fetched", "provided_file_not_inspected", "checksum_recorded", "inspected_elsewhere"}:
            self.error(path, "source_lock_evidence evidence retrieval_status is invalid")
        sha256 = str(source.get("sha256", "")).strip()
        if sha256 and not re.fullmatch(r"[a-fA-F0-9]{64}", sha256):
            self.error(path, "source_lock_evidence evidence sha256 must be 64 hex characters")
        if source.get("retrieval_status") == "checksum_recorded" and artifact_kind in {"step", "stp"} and not sha256:
            self.error(path, "checksum_recorded STEP/STP evidence must include sha256")
        if not locator:
            self.error(path, "source_lock_evidence evidence source locator must be non-empty")
            return
        if not isinstance(trusted_for, list) or not trusted_for:
            self.error(path, "source_lock_evidence evidence source trusted_for must be non-empty")
        else:
            allowed_trust = {"layout", "geometry_reference", "source_identity", "procurement_identity", "critical_dimensions", "review_only"}
            unsupported = sorted({str(item) for item in trusted_for} - allowed_trust)
            if unsupported:
                self.error(path, f"source_lock_evidence evidence trusted_for contains unsupported values: {', '.join(unsupported)}")
        if artifact_kind in {"step", "stp"} and "geometry_reference" not in trusted_for:
            self.error(path, "STEP/STP evidence must be trusted for geometry_reference")
        if source_type in {"step_parts", "manufacturer", "datasheet", "other"}:
            parsed = urlparse(locator)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                self.error(path, f"{source_type} evidence locator must be an http(s) URL")
                return
            host = parsed.netloc.lower()
            if source_type == "step_parts" and not is_step_parts_host_or_asset(host, parsed.path):
                self.error(path, "step_parts evidence locator must use step.parts API/site or the step.parts media asset origin")
            if source_type == "manufacturer" and host in {"step.parts", "www.step.parts"}:
                self.error(path, "manufacturer evidence locator must not use the step.parts domain")

    def validate_review_bundle_document(self, path: Path, document: dict[str, Any]) -> None:
        if not document.get("artifacts"):
            self.error(path, "review_bundle artifacts must be non-empty")
        if not document.get("reports"):
            self.error(path, "review_bundle reports must be non-empty")
        if not document.get("locked_layout_facts"):
            self.error(path, "review_bundle locked_layout_facts must be non-empty")
        policy_text = " ".join(str(item).lower() for item in document.get("evidence_policy", []))
        if "review" not in policy_text or "geometry" not in policy_text:
            self.error(path, "review_bundle evidence_policy must distinguish review evidence from geometry checks")
        for target in document.get("viewer_targets", []):
            if not isinstance(target, dict):
                self.error(path, "review_bundle viewer_targets entries must be objects")
                continue
            if target.get("evidence_role") != "review_only":
                self.error(path, "review_bundle viewer_targets must use review_only evidence_role")

    def validate_interface_frame_document(self, path: Path, document: dict[str, Any]) -> None:
        for field in ["part_id", "role", "frame", "locked_fact_refs", "tolerance"]:
            if field not in document:
                self.error(path, f"interface_frame missing {field}")
        frame = document.get("frame")
        if not isinstance(frame, dict):
            self.error(path, "interface_frame.frame must be an object")
        else:
            for axis in ["origin", "x_axis", "y_axis", "z_axis"]:
                if not is_vector3(frame.get(axis)):
                    self.error(path, f"interface_frame.frame.{axis} must be a 3-number vector")
        if not isinstance(document.get("locked_fact_refs"), list):
            self.error(path, "interface_frame.locked_fact_refs must be a list")
        tolerance = document.get("tolerance")
        if not isinstance(tolerance, dict):
            self.error(path, "interface_frame.tolerance must be an object")
        else:
            for field in ["position_mm", "angle_deg"]:
                if not isinstance(tolerance.get(field), (int, float)) or tolerance[field] < 0:
                    self.error(path, f"interface_frame.tolerance.{field} must be a non-negative number")

    def validate_replacement_plan_document(self, path: Path, document: dict[str, Any]) -> None:
        if not isinstance(document.get("source_scene_id"), str) or not document["source_scene_id"]:
            self.error(path, "replacement_plan.source_scene_id must be a non-empty string")
        replacements = document.get("replacements")
        if not isinstance(replacements, list):
            self.error(path, "replacement_plan.replacements must be a list")
            replacements = []
        if not nonempty_string_list(document.get("inspection_required")):
            self.error(path, "replacement_plan.inspection_required must be a non-empty string list")
        for index, replacement in enumerate(replacements):
            if not isinstance(replacement, dict):
                self.error(path, f"replacement_plan.replacements[{index}] must be an object")
                continue
            for field in ["part_id", "mode", "proxy_frame_id", "source_frame_id", "transform", "locked_fact_refs", "required_checks", "status"]:
                if field not in replacement:
                    self.error(path, f"replacement_plan.replacements[{index}] missing {field}")
            transform = replacement.get("transform")
            if isinstance(transform, dict):
                if not is_vector3(transform.get("position")):
                    self.error(path, f"replacement_plan.replacements[{index}].transform.position must be a 3-number vector")
                if not is_vector3(transform.get("rotation")):
                    self.error(path, f"replacement_plan.replacements[{index}].transform.rotation must be a 3-number vector")
            else:
                self.error(path, f"replacement_plan.replacements[{index}].transform must be an object")
            if not isinstance(replacement.get("locked_fact_refs"), list):
                self.error(path, f"replacement_plan.replacements[{index}].locked_fact_refs must be a list")
            if not nonempty_string_list(replacement.get("required_checks")):
                self.error(path, f"replacement_plan.replacements[{index}].required_checks must be a non-empty string list")

    def validate_detail_shape_plan_document(self, path: Path, document: dict[str, Any]) -> None:
        for field in ["source_spec_id", "part_id"]:
            if not isinstance(document.get(field), str) or not document[field]:
                self.error(path, f"detail_shape_plan.{field} must be a non-empty string")
        if not nonempty_string_list(document.get("locked_interfaces")):
            self.error(path, "detail_shape_plan.locked_interfaces must be a non-empty string list")
        if not isinstance(document.get("protected_zones"), list):
            self.error(path, "detail_shape_plan.protected_zones must be a list")
        if not isinstance(document.get("feature_plan"), list):
            self.error(path, "detail_shape_plan.feature_plan must be a list")
        if not nonempty_string_list(document.get("inspection_required")):
            self.error(path, "detail_shape_plan.inspection_required must be a non-empty string list")
        intent = document.get("shape_intent")
        if not isinstance(intent, dict):
            self.error(path, "detail_shape_plan.shape_intent must be an object")
        else:
            for field in ["style", "manufacturing", "avoid"]:
                if field not in intent:
                    self.error(path, f"detail_shape_plan.shape_intent missing {field}")
            if not isinstance(intent.get("wall_min_mm"), (int, float)) or intent["wall_min_mm"] < 0:
                self.error(path, "detail_shape_plan.shape_intent.wall_min_mm must be a non-negative number")


def walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(walk_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(walk_keys(child))
        return keys
    return set()


def is_vector3(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(isinstance(item, (int, float)) for item in value)


def nonempty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def is_step_parts_host_or_asset(host: str, path: str) -> bool:
    if host in {"step.parts", "www.step.parts", "api.step.parts"}:
        return True
    if host == "media.githubusercontent.com" and "/earthtojake/step.parts/" in path:
        return True
    return False


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Zen CAD contract schemas, registry records, and optional contract packages.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, help="Optional JSON file or directory containing contract documents.")
    parser.add_argument("--repo-only", action="store_true", help="Validate only repository schemas and registry.")
    parser.add_argument("--package-only", action="store_true", help="Validate only the package passed with --package.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    validator = ContractValidator(args.repo_root)

    if args.package_only and not args.package:
        validator.error("<args>", "--package-only requires --package")
    if not args.package_only:
        validator.validate_repo()
    if args.package and not args.repo_only:
        validator.validate_package(args.package)

    if validator.issues:
        for issue in validator.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1

    print("Zen CAD contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
