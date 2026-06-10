#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"


@dataclass
class ViewerSnapshotResult:
    snapshot_path: Path
    report_path: Path


class ViewerSnapshotCapturer:
    def __init__(self, repo_root: Path, viewer_url: str, out: Path, report: Path, viewer_root: Path, timeout_ms: int) -> None:
        self.repo_root = repo_root
        self.viewer_url = force_real_canvas_url(viewer_url)
        self.out = out
        self.report = report
        self.viewer_root = viewer_root
        self.timeout_ms = timeout_ms
        self.issues: list[Issue] = []

    def error(self, path: Path | str, message: str) -> None:
        self.issues.append(Issue(str(path), message))

    def capture(self) -> ViewerSnapshotResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        if validator.issues:
            self.issues.extend(validator.issues)
            return None
        if not self.viewer_root.exists():
            self.error(self.viewer_root, "viewer root does not exist")
            return None
        if not (self.viewer_root / "node_modules" / "playwright").exists():
            self.error(self.viewer_root, "viewer root must have node_modules/playwright installed")
            return None

        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.report.parent.mkdir(parents=True, exist_ok=True)
        run = self.run_playwright()
        status_line = str(run.get("statusLine", ""))
        snapshot_written = self.out.exists() and self.out.stat().st_size > 0
        ok = bool(run.get("ok")) and bool(run.get("canvasPresent")) and snapshot_written
        checks = [
            check_result("viewer_url_opened", "viewer", bool(run.get("opened")), f"url={self.viewer_url}"),
            check_result("viewer_model_loaded", "viewer", bool(run.get("ok")), status_line or "viewer did not report Loaded"),
            check_result(
                "viewer_canvas_present",
                "viewer",
                bool(run.get("canvasPresent")),
                f"canvas_box={run.get('canvasBox', '')}",
            ),
            check_result(
                "snapshot_file_written",
                "snapshot",
                snapshot_written,
                f"snapshot={self.out}; bytes={self.out.stat().st_size if self.out.exists() else 0}",
            ),
        ]
        report = {
            "schema_version": SCHEMA_VERSION,
            "kind": "inspection_report",
            "id": f"{self.out.stem}.viewer_snapshot_report",
            "spec_id": "viewer_snapshot",
            "artifact": {"path": str(self.out), "kind": "snapshot"},
            "status": "passed" if ok else "failed",
            "checks": checks,
            "skipped_checks": [],
            "repair_attempts": [],
            "proceed_recommendation": "ready_for_proceed_review" if ok else "needs_repair",
            "limitations": [
                "Viewer snapshots are review evidence only and do not replace geometry checks.",
            ],
            "extensions": {
                "capturer": "tools/capture_viewer_snapshot.py",
                "viewer_url": self.viewer_url,
                "viewer_root": str(self.viewer_root),
                "status_line": status_line,
            },
        }
        write_json(self.report, report)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.report)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None
        if not ok:
            self.error(self.out, status_line or "viewer snapshot capture failed")
            return None
        return ViewerSnapshotResult(snapshot_path=self.out, report_path=self.report)

    def run_playwright(self) -> dict[str, Any]:
        script = """
import { chromium } from 'playwright';
const [viewerUrl, out, timeoutText] = process.argv.slice(2);
const timeout = Number(timeoutText || 45000);
const result = { opened: false, ok: false, statusLine: '', canvasPresent: false, canvasBox: '' };
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(viewerUrl, { waitUntil: 'domcontentloaded', timeout });
  result.opened = true;
  await page.waitForFunction(
    () => document.body.innerText.includes('Loaded') || document.body.innerText.includes('Could not load'),
    null,
    { timeout }
  );
  const bodyText = await page.locator('body').innerText();
  result.statusLine = bodyText.split('\\n').find((line) => line.includes('Loaded') || line.includes('Could not load')) || '';
  result.ok = result.statusLine.includes('Loaded');
  if (result.ok) {
    try {
      await page.getByRole('button', { name: /Shaded \\+ Wire/i }).click({ timeout: 2000 });
    } catch {}
    try {
      await page.getByRole('button', { name: /Fit model to view/i }).click({ timeout: 2000 });
    } catch {}
    await page.waitForTimeout(1000);
  }
  try {
    await page.waitForSelector('canvas', { timeout: Math.min(timeout, 10000) });
    const canvas = page.locator('canvas').first();
    const box = await canvas.boundingBox();
    result.canvasPresent = Boolean(box && box.width > 100 && box.height > 100);
    result.canvasBox = box ? `${Math.round(box.width)}x${Math.round(box.height)}` : '';
  } catch {
    result.canvasPresent = false;
  }
  await page.screenshot({ path: out, fullPage: false });
} finally {
  await browser.close();
}
process.stdout.write(JSON.stringify(result));
"""
        fd, script_name = tempfile.mkstemp(prefix=".zen-cad-capture-", suffix=".mjs", dir=self.viewer_root)
        os.close(fd)
        script_path = Path(script_name)
        try:
            script_path.write_text(script, encoding="utf-8")
            completed = subprocess.run(
                ["node", str(script_path), self.viewer_url, str(self.out), str(self.timeout_ms)],
                cwd=self.viewer_root,
                text=True,
                capture_output=True,
                check=False,
            )
        finally:
            script_path.unlink(missing_ok=True)
        if completed.returncode != 0 and not completed.stdout:
            return {"opened": False, "ok": False, "statusLine": completed.stderr.strip()}
        try:
            loaded = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return {"opened": False, "ok": False, "statusLine": completed.stderr.strip() or completed.stdout.strip()}
        return loaded if isinstance(loaded, dict) else {"opened": False, "ok": False, "statusLine": "invalid capture result"}


def check_result(check_id: str, check_type: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "check_type": check_type,
        "status": "passed" if passed else "failed",
        "evidence": evidence,
        "locked_fact_refs": [],
    }


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def force_real_canvas_url(viewer_url: str) -> str:
    parsed = urlparse(viewer_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("realCanvas", "1")
    return urlunparse(parsed._replace(query=urlencode(query)))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a local CAD Viewer snapshot for a generated STEP artifact.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--viewer-url", required=True, help="CAD Viewer URL to open.")
    parser.add_argument("--viewer-root", type=Path, required=True, help="CAD-Visualizer project root with Playwright installed.")
    parser.add_argument("--out", type=Path, required=True, help="Output PNG snapshot path.")
    parser.add_argument("--report", type=Path, required=True, help="Output inspection report path.")
    parser.add_argument("--timeout-ms", type=int, default=45000, help="Browser wait timeout in milliseconds.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    capturer = ViewerSnapshotCapturer(args.repo_root, args.viewer_url, args.out, args.report, args.viewer_root, args.timeout_ms)
    result = capturer.capture()
    if capturer.issues:
        for issue in capturer.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("viewer snapshot capture failed", file=sys.stderr)
        return 1
    print(f"Viewer snapshot: {result.snapshot_path}")
    print(f"Inspection report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
