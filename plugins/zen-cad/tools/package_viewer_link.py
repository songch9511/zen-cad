#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlencode


@dataclass
class ViewerLinkResult:
    html_path: Path
    viewer_url: str
    served_step_path: Path | None


class ViewerLinkPackager:
    def __init__(
        self,
        step: Path,
        out: Path,
        viewer_base_url: str,
        viewer_public_dir: Path | None,
    ) -> None:
        self.step = step
        self.out = out
        self.viewer_base_url = viewer_base_url.rstrip("/")
        self.viewer_public_dir = viewer_public_dir
        self.issues: list[str] = []

    def error(self, message: str) -> None:
        self.issues.append(message)

    def package(self) -> ViewerLinkResult | None:
        if not self.step.exists():
            self.error(f"STEP artifact does not exist: {self.step}")
            return None
        if self.step.stat().st_size <= 0:
            self.error(f"STEP artifact is empty: {self.step}")
            return None

        served_step_path: Path | None = None
        served_model_path: str | None = None
        if self.viewer_public_dir is not None:
            served_step_path, served_model_path = self.copy_into_viewer_public_dir()

        if served_model_path:
            viewer_url = f"{self.viewer_base_url}/?{urlencode({'model': served_model_path, 'label': self.step.name, 'realCanvas': '1'})}"
            mode = "auto_load"
        else:
            viewer_url = f"{self.viewer_base_url}/"
            mode = "manual_load"

        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.out.write_text(render_html(self.step, viewer_url, mode, served_step_path), encoding="utf-8")
        return ViewerLinkResult(html_path=self.out, viewer_url=viewer_url, served_step_path=served_step_path)

    def copy_into_viewer_public_dir(self) -> tuple[Path | None, str | None]:
        public_dir = self.viewer_public_dir
        if public_dir is None:
            return None, None
        if not public_dir.exists():
            self.error(f"viewer public directory does not exist: {public_dir}")
            return None, None
        digest = hashlib.sha256(str(self.step.resolve()).encode("utf-8")).hexdigest()[:10]
        safe_stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in self.step.stem)
        target_dir = public_dir / "zen-cad-artifacts"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{safe_stem}-{digest}{self.step.suffix.lower()}"
        shutil.copy2(self.step, target)
        return target, f"/zen-cad-artifacts/{quote(target.name)}"


def render_html(step: Path, viewer_url: str, mode: str, served_step_path: Path | None) -> str:
    served = str(served_step_path) if served_step_path is not None else ""
    title = f"Zen CAD viewer link: {step.name}"
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{html.escape(title)}</title>",
            "  <style>",
            "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 32px; line-height: 1.5; }",
            "    code { background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }",
            "    a { color: #0f766e; font-weight: 650; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{html.escape(step.name)}</h1>",
            f"  <p><a href=\"{html.escape(viewer_url)}\">Open in CAD Viewer</a></p>",
            f"  <p>Mode: <code>{html.escape(mode)}</code></p>",
            f"  <p>Generated STEP: <code>{html.escape(str(step))}</code></p>",
            f"  <p>Served STEP: <code>{html.escape(served or 'not copied; use the viewer file picker')}</code></p>",
            "  <p>This link is review evidence only. Geometry checks and inspection reports remain the completion evidence.</p>",
            "</body>",
            "</html>",
            "",
        ]
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package a local CAD Viewer link for a generated STEP artifact.")
    parser.add_argument("--step", type=Path, required=True, help="Generated STEP/STP artifact.")
    parser.add_argument("--out", type=Path, required=True, help="Output viewer_link.html path.")
    parser.add_argument("--viewer-base-url", default="http://localhost:5173", help="Local CAD Viewer base URL.")
    parser.add_argument("--viewer-public-dir", type=Path, help="Optional CAD-Visualizer public directory for auto-load URLs.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    packager = ViewerLinkPackager(args.step, args.out, args.viewer_base_url, args.viewer_public_dir)
    result = packager.package()
    if packager.issues:
        for issue in packager.issues:
            print(issue, file=sys.stderr)
        return 1
    if result is None:
        print("viewer link packaging failed", file=sys.stderr)
        return 1
    print(f"Viewer link: {result.html_path}")
    print(f"Viewer URL: {result.viewer_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
