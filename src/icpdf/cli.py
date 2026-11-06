"""CLI surface (skeleton).

Phase 0 only implements `init`; parse/render/tables/candidates/extract/report
are declared now so the command surface is frozen before Phase 1.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help="icpdf-extractor CLI")


def _not_implemented(name: str) -> None:
    typer.secho(
        f"`{name}` is not implemented in Phase 0 (contract-only round).",
        fg=typer.colors.YELLOW,
        err=True,
    )
    raise typer.Exit(code=2)


@app.command()
def init(runs: Path = typer.Option(Path("runs"), help="runtime artifact root")) -> None:
    """Create the local artifact root."""
    runs.mkdir(parents=True, exist_ok=True)
    typer.secho(f"initialized: {runs.resolve()}", fg=typer.colors.GREEN)


@app.command()
def parse(pdf: Path = typer.Option(..., help="source PDF"),
          mpn: str = typer.Option(..., help="requested MPN"),
          runs: Path = typer.Option(Path("runs"), help="artifact root"),
          dpi: float = typer.Option(0.0, help="render DPI; 0 = use parser config"),
          config: Path | None = typer.Option(None, help="parser YAML config")) -> None:
    """Parse a PDF into deterministic artifacts (Phase 1)."""
    from icpdf.parser.pipeline import parse_pdf
    result = parse_pdf(pdf, mpn, runs, dpi=(dpi or None), config_path=config)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command()
def render(run_id: str = typer.Option(..., help="run id"),
           page: int = typer.Option(1, help="1-based page"),
           runs: Path = typer.Option(Path("runs"), help="artifact root")) -> None:
    from icpdf.parser.page_renderer import render_page
    run_dir = runs / run_id
    out = run_dir / "pages" / f"render-{page:04d}.png"
    geometry = render_page(run_dir / "source.pdf", page, out)
    typer.echo(json.dumps({"png": str(out),
                           "geometry": geometry.model_dump(mode="json")},
                          ensure_ascii=False, indent=2))


@app.command()
def tables(run_id: str = typer.Option(..., help="run id"),
           runs: Path = typer.Option(Path("runs"), help="artifact root")) -> None:
    data = json.loads((runs / run_id / "tables.json").read_text(encoding="utf-8"))
    for table in data:
        typer.echo(f"{table['table_id']}  p{table['page_number']}  "
                   f"{table['table_type']}  {table['reconstruction_status']}  "
                   f"rows={len(table['rows'])}  conf={table['confidence']}")


@app.command()
def candidates(run_id: str = typer.Option(..., help="run id"),
               runs: Path = typer.Option(Path("runs"), help="artifact root")) -> None:
    data = json.loads((runs / run_id / "candidates.json").read_text(encoding="utf-8"))
    items = data.get("candidates") or []
    by_table: dict[str, int] = {}
    for item in items:
        by_table[item["table_id"]] = by_table.get(item["table_id"], 0) + 1
    typer.echo(json.dumps({"total": len(items), "by_table": by_table},
                          ensure_ascii=False, indent=2))


@app.command()
def extract(run_id: str = typer.Option(..., help="run id")) -> None:
    _not_implemented("extract")


@app.command()
def report(run_id: str = typer.Option(..., help="run id"),
           runs: Path = typer.Option(Path("runs"), help="artifact root")) -> None:
    data = json.loads((runs / run_id / "run_manifest.json").read_text(encoding="utf-8"))
    typer.echo(json.dumps({k: data.get(k) for k in (
        "run_id", "document_sha256", "requested_mpn", "page_count",
        "table_count", "candidate_count", "parser_version", "contract_version")},
        ensure_ascii=False, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
