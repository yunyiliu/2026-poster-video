#!/usr/bin/env python3
"""Convert a .pptx (or .key, .pdf) into a slides/ folder of PNGs.

Tries these converters in order, depending on what is installed:
    1. LibreOffice (`soffice` / `libreoffice`) → PDF, then pdftoppm → PNG.
    2. macOS Keynote via AppleScript → PDF, then pdftoppm → PNG.
    3. If input is already a PDF, skip the conversion and only rasterize.

Requirements:
    - `pdftoppm` (from poppler — `brew install poppler`).
    - At least one of:
        * LibreOffice (`brew install --cask libreoffice`) — cross-platform.
        * Keynote (macOS, free, preinstalled on most Macs).

Usage:
    python3 import_pptx.py --input /path/to/deck.pptx --slides-dir ./slides
    python3 import_pptx.py --input /path/to/deck.pdf  --slides-dir ./slides --dpi 200
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

KEYNOTE_APPLESCRIPT = """
on run argv
    set thePPTX to item 1 of argv
    set thePDF  to item 2 of argv
    tell application "Keynote"
        activate
        set theDoc to open POSIX file thePPTX
        delay 0.5
        export theDoc as PDF to POSIX file thePDF
        close theDoc saving no
    end tell
end run
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert a deck file into a slides/ PNG set.")
    p.add_argument("--input", required=True, help="Input .pptx, .key, or .pdf file.")
    p.add_argument("--slides-dir", required=True, help="Output directory for PNGs.")
    p.add_argument("--dpi", type=int, default=200, help="Rasterization DPI (default 200).")
    p.add_argument("--prefix", default="", help="Filename prefix (e.g. 'slide-').")
    return p.parse_args()


def have(*names: str) -> str | None:
    for n in names:
        path = shutil.which(n)
        if path:
            return path
    return None


def convert_to_pdf(src: Path, tmp_dir: Path) -> Path:
    if src.suffix.lower() == ".pdf":
        return src

    pdf_out = tmp_dir / (src.stem + ".pdf")

    so = have("soffice", "libreoffice")
    if so:
        print(f"  using LibreOffice ({so}) for {src.name} -> PDF")
        subprocess.run(
            [so, "--headless", "--convert-to", "pdf",
             "--outdir", str(tmp_dir), str(src)],
            check=True, stdout=subprocess.DEVNULL,
        )
        if pdf_out.exists():
            return pdf_out

    if Path("/Applications/Keynote.app").exists():
        print(f"  using Keynote for {src.name} -> PDF")
        with tempfile.NamedTemporaryFile(
            "w", suffix=".applescript", delete=False
        ) as f:
            f.write(KEYNOTE_APPLESCRIPT)
            script_path = f.name
        subprocess.run(
            ["osascript", script_path, str(src.resolve()), str(pdf_out.resolve())],
            check=True,
        )
        if pdf_out.exists():
            return pdf_out

    raise SystemExit(
        "No PPTX-to-PDF converter found.\n"
        "Install LibreOffice:  brew install --cask libreoffice\n"
        "  or ensure Keynote is installed (macOS, free).\n"
        "  or export the deck to PDF yourself and pass --input deck.pdf"
    )


def rasterize_pdf(pdf: Path, slides_dir: Path, dpi: int, prefix: str) -> int:
    if not have("pdftoppm"):
        raise SystemExit(
            "`pdftoppm` not found. Install poppler:  brew install poppler"
        )
    slides_dir.mkdir(parents=True, exist_ok=True)
    out_root = slides_dir / f"{prefix}slide"
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi),
         str(pdf), str(out_root)],
        check=True,
    )
    # pdftoppm names files `<root>-1.png`, `<root>-2.png`, ...
    # Rename to two-digit zero-padded `01.png`, `02.png`, ... so that
    # render_video.py picks them up in order.
    renamed = 0
    for src in sorted(slides_dir.glob(f"{prefix}slide-*.png")):
        try:
            num = int(src.stem.rsplit("-", 1)[1])
        except (IndexError, ValueError):
            continue
        dst = slides_dir / f"{prefix}{num:02d}.png"
        if dst.exists() and dst != src:
            dst.unlink()
        src.rename(dst)
        renamed += 1
    return renamed


def main() -> None:
    args = parse_args()
    src = Path(args.input).expanduser().resolve()
    slides_dir = Path(args.slides_dir).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Missing input file: {src}")

    with tempfile.TemporaryDirectory(prefix="pptx-import-") as tmp:
        tmp_dir = Path(tmp)
        pdf = convert_to_pdf(src, tmp_dir)
        count = rasterize_pdf(pdf, slides_dir, args.dpi, args.prefix)

    print(f"Wrote {count} slide image(s) into {slides_dir}")


if __name__ == "__main__":
    main()
