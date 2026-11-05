"""Evaluate a parser run against the Phase 1.2 gold table set.

Usage:
    python -m tools.goldset.evaluate \
        --gold gold/gold_table_set.jsonl \
        --run runs/phase11_audit/20261105T124640Z-16e592 \
        --run runs/phase11_audit/20261105T124706Z-b154f5 \
        --run runs/phase11_audit/20261105T124735Z-1ab90a \
        --label baseline-1d8c722 \
        --out gold/baseline_report.md \
        --json gold/baseline_report.json

Matching protocol (see gold/README.md):
* same page, one-to-one greedy matching by descending IoU, IoU >= 0.5;
* predictions overlapping an annotated region (intersection / prediction area
  >= 0.25) but matching no gold table count as false positives;
* predictions on gold pages entirely outside annotated regions are reported
  separately and are not scored.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IOU_MATCH = 0.5
IOU_SCOPE = 0.25

COARSE_ROLE = {
    "min": "min",
    "typ": "typ",
    "max": "max",
    "unit": "unit",
    "condition": "condition",
    "test": "condition",
    "symbol": "symbol",
    "parameter": "symbol",
    "name": "symbol",
    "signal": "symbol",
    "group": "symbol",
    "unknown": "unknown",
}
BASELINE_ROLES = {"min", "typ", "max", "unit", "condition", "symbol", "value", "unknown"}
CELL_SUFFIX = re.compile(r"-c(\d+)$")


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _compact(text: str) -> str:
    """Whitespace-free form for header labels.

    PDF text extraction splits subscripts and superscripts into separate
    spans (``f CLK`` for ``fCLK``, ``V RMS`` spacing in ``VRMS``), so header
    attribution ignores intra-label spacing.  Word boundaries are still
    preserved by :func:`_norm` for body-cell scoring.
    """
    return _norm(text).replace(" ", "")


def _area(box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _intersection(a, b) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * \
        max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _iou(a, b) -> float:
    inter = _intersection(a, b)
    union = _area(a) + _area(b) - inter
    return inter / union if union > 0 else 0.0


def _over_pred(a, b) -> float:
    """Intersection over the prediction area; 0 when the prediction is empty."""
    area = _area(a)
    return _intersection(a, b) / area if area > 0 else 0.0


def _prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def _load_gold(path: Path) -> tuple[list[dict], list[dict], dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    tables = [r for r in records if r["kind"] == "table"
              and r["human_verdict"] == "accepted"]
    negatives = [r for r in records if r["kind"] == "negative"
                 and r["human_verdict"] == "accepted"]
    excluded = [r["item_id"] for r in records if r["human_verdict"] != "accepted"]
    return tables, negatives, {"excluded": excluded, "records": len(records)}


def _load_run(run_dir: Path) -> dict:
    document = json.loads((run_dir / "document.json").read_text(encoding="utf-8"))
    tables = json.loads((run_dir / "tables.json").read_text(encoding="utf-8"))
    candidates_path = run_dir / "candidates.json"
    candidates = []
    if candidates_path.exists():
        candidates = json.loads(candidates_path.read_text(encoding="utf-8"))["candidates"]
    config_path = run_dir / "run_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    return {
        "run_dir": str(run_dir),
        "run_id": run_dir.name,
        "sha256": document["sha256"],
        "tables": tables,
        "candidates": candidates,
        "parser_config_sha256": config.get("parser_config_sha256"),
        "parser_version": config.get("parser_version"),
    }


def _prediction_columns(table: dict) -> int:
    columns = [cell.get("column_id") for row in table["rows"] for cell in row["cells"]
               if cell.get("column_id") is not None]
    return max(columns) + 1 if columns else 0


def _predicted_roles(run: dict) -> dict[tuple[str, int], str]:
    counts: dict[tuple[str, int], Counter] = defaultdict(Counter)
    for candidate in run["candidates"]:
        match = CELL_SUFFIX.search(candidate["cell_id"])
        if not match:
            continue
        counts[(candidate["table_id"], int(match.group(1)))][candidate["column_role"]] += 1
    roles: dict[tuple[str, int], str] = {}
    for key, counter in counts.items():
        roles[key] = counter.most_common(1)[0][0]
    return roles


def _cell_texts(rows: list[dict]) -> list[str]:
    texts = []
    for row in rows:
        for cell in row["cells"]:
            text = _norm(cell["text"])
            if text:
                texts.append(text)
    return texts


def _gold_cell_texts(table: dict) -> list[str]:
    texts = [_norm(cell["text"]) for cell in table["cells"]]
    return [text for text in texts if text]


def _multiset_f1(gold: list[str], pred: list[str]) -> tuple[int, int, int]:
    gold_counter, pred_counter = Counter(gold), Counter(pred)
    tp = sum((gold_counter & pred_counter).values())
    return tp, sum(pred_counter.values()) - tp, sum(gold_counter.values()) - tp


def _score_pair(gold: dict, pred: dict, roles: dict[tuple[str, int], str]) -> dict:
    gold_table = gold["table"]
    gold_rows = gold_table["n_rows"]
    gold_columns = gold_table["n_columns"]
    pred_rows = len(pred["rows"])
    pred_columns = _prediction_columns(pred)

    gold_text = _gold_cell_texts(gold_table)
    pred_text = _cell_texts(pred["rows"])
    text_tp, text_fp, text_fn = _multiset_f1(gold_text, pred_text)

    gold_headers = [_norm(h) for h in gold_table["headers"]]
    pred_headers = [_norm(h) for h in pred.get("headers") or []]
    gold_keys = [_compact(h) for h in gold_headers]
    pred_keys = [_compact(h) for h in pred_headers]
    comparable = pred_columns == gold_columns and len(pred_headers) == gold_columns
    # Column attribution is scored over gold columns that actually carry a
    # label; an empty gold label is annotation debt, not a predicted miss.
    labeled_columns = [index for index, key in enumerate(gold_keys) if key]
    if comparable:
        header_hits = sum(1 for index in labeled_columns
                          if gold_keys[index] == pred_keys[index])
        header_hits_strict = sum(1 for index in labeled_columns
                                 if gold_headers[index] == pred_headers[index])
        header_exact = header_hits == len(labeled_columns)
        header_tp, header_fp, header_fn = _multiset_f1(
            [key for key in gold_keys if key], [key for key in pred_keys if key])
    else:
        header_hits = header_hits_strict = 0
        header_exact = False
        header_tp = header_fp = 0
        header_fn = len(labeled_columns)

    gold_roles = [COARSE_ROLE.get(role, "value") for role in gold_table["column_roles"]]
    pred_roles = [roles.get((pred["table_id"], column), "unknown")
                  for column in range(pred_columns)]
    role_length_ok = pred_columns == gold_columns
    role_hits = sum(1 for g, p in zip(gold_roles, pred_roles)
                    if role_length_ok and g == p)
    gold_header_rows = int(gold_table.get("header_rows", 0))
    pred_header_rows = int(pred.get("header_rows", 0) or 0)

    return {
        "rows": {"gold": gold_rows, "pred": pred_rows,
                 "exact": gold_rows == pred_rows,
                 "error": pred_rows - gold_rows},
        "columns": {"gold": gold_columns, "pred": pred_columns,
                    "exact": gold_columns == pred_columns,
                    "error": pred_columns - gold_columns},
        "cells": {"gold": len(gold_text), "pred": len(pred_text),
                  "tp": text_tp, "fp": text_fp, "fn": text_fn},
        "headers": {"column_hits": header_hits, "column_hits_strict": header_hits_strict,
                    "columns": len(labeled_columns), "labeled_columns": labeled_columns,
                    "all_exact": header_exact, "comparable": comparable,
                    "gold_rows": gold_header_rows, "pred_rows": pred_header_rows,
                    "row_depth_exact": gold_header_rows == pred_header_rows,
                    "cell_text_tp": header_tp, "cell_text_fp": header_fp,
                    "cell_text_fn": header_fn,
                    "header_path_present": bool(pred.get("header_path")),
                    "gold_text": gold_table["headers"],
                    "pred_text": pred.get("headers") or []},
        "roles": {"column_hits": role_hits, "columns": gold_columns,
                  "all_exact": role_length_ok and role_hits == gold_columns,
                  "gold": gold_roles, "pred": pred_roles,
                  "comparable": role_length_ok},
        "table_type": {"gold": gold_table["table_type"],
                       "pred": pred["table_type"],
                       "exact": gold_table["table_type"] == pred["table_type"]},
        "reconstruction_status": pred.get("reconstruction_status"),
    }


def _match_page(gold_tables: list[dict], predictions: list[dict]) -> dict[str, tuple[dict, float]]:
    pairs = []
    for gold in gold_tables:
        gold_box = gold["table"]["bbox"]
        for pred in predictions:
            score = _iou(gold_box, pred["bbox"])
            if score >= IOU_MATCH:
                pairs.append((score, gold["item_id"], pred["table_id"]))
    pairs.sort(key=lambda item: (-item[0], item[1], item[2]))
    matched_gold: dict[str, tuple[dict, float]] = {}
    used_pred: set[str] = set()
    for score, item_id, table_id in pairs:
        if item_id in matched_gold or table_id in used_pred:
            continue
        pred = next(p for p in predictions if p["table_id"] == table_id)
        matched_gold[item_id] = (pred, score)
        used_pred.add(table_id)
    return matched_gold


FOCUS_ROLES = ("min", "typ", "max", "unit", "condition", "symbol", "value", "unknown")


def _confusion_matrix(pairs: list[tuple[str, str]], labels: list[str]) -> dict:
    matrix = {row: {column: 0 for column in labels} for row in labels}
    for gold, pred in pairs:
        if gold not in matrix:
            matrix[gold] = {column: 0 for column in labels}
        if pred not in matrix[gold]:
            matrix[gold][pred] = 0
        matrix[gold][pred] += 1
    return matrix


def _role_metrics(matched_details: list[dict]) -> dict:
    """Column-role precision/recall per role over comparable matched tables.

    The unit of account is one gold column.  ``pred`` counts columns predicted
    with the role; ``gold`` counts gold columns annotated with it.
    """
    stats = {role: {"gold": 0, "pred": 0, "tp": 0, "fp": 0, "fn": 0}
             for role in FOCUS_ROLES}
    pairs: list[tuple[str, str]] = []
    for item in matched_details:
        roles = item["structure"]["roles"]
        if not roles["comparable"]:
            continue
        for gold, pred in zip(roles["gold"], roles["pred"]):
            gold = gold if gold in stats else "value"
            pred = pred if pred in stats else "unknown"
            pairs.append((gold, pred))
            stats[gold]["gold"] += 1
            stats[pred]["pred"] += 1
            if gold == pred:
                stats[gold]["tp"] += 1
            else:
                stats[pred]["fp"] += 1
                stats[gold]["fn"] += 1
    for entry in stats.values():
        precision = entry["tp"] / (entry["tp"] + entry["fp"]) if entry["tp"] + entry["fp"] else 0.0
        recall = entry["tp"] / (entry["tp"] + entry["fn"]) if entry["tp"] + entry["fn"] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        entry["precision"] = round(precision, 4)
        entry["recall"] = round(recall, 4)
        entry["f1"] = round(f1, 4)
    return {
        "by_role": stats,
        "confusion": _confusion_matrix(pairs, list(FOCUS_ROLES)),
    }


def evaluate(gold_tables: list[dict], negatives: list[dict], runs: list[dict],
             label: str, annotation_version: str, baseline: dict | None = None) -> dict:
    by_pdf: dict[str, list[dict]] = defaultdict(list)
    for table in gold_tables:
        by_pdf[table["pdf_id"]].append(table)
    neg_by_pdf: dict[str, list[dict]] = defaultdict(list)
    for negative in negatives:
        neg_by_pdf[negative["pdf_id"]].append(negative)

    runs_by_sha = {run["sha256"]: run for run in runs}
    pdf_ids = {table["pdf_id"] for table in gold_tables}
    used_runs = {}
    for pdf_id in pdf_ids:
        sha = next(table["pdf_sha256"] for table in gold_tables if table["pdf_id"] == pdf_id)
        if sha not in runs_by_sha:
            raise SystemExit(f"no run supplied for {pdf_id} ({sha})")
        used_runs[pdf_id] = runs_by_sha[sha]

    details = []
    per_pdf_rows = {}
    total_tp = total_fp = total_fn = 0
    total_out_of_scope = 0
    total_preds_on_gold_pages = 0
    negative_rows = []
    fp_rows = []
    run_status = defaultdict(Counter)

    for pdf_id, gold_list in sorted(by_pdf.items()):
        run = used_runs[pdf_id]
        roles = _predicted_roles(run)
        gold_pages = {table["page"] for table in gold_list}
        gold_pages |= {negative["page"] for negative in neg_by_pdf[pdf_id]}
        preds_by_page: dict[int, list[dict]] = defaultdict(list)
        for pred in run["tables"]:
            preds_by_page[pred["page_number"]].append(pred)

        tp = fp = fn = out_of_scope = 0
        matched_pairs: dict[str, tuple[dict, float]] = {}
        fragment_counts: dict[str, int] = {}
        page_pred_totals = {}
        for page in sorted(gold_pages):
            page_gold = [table for table in gold_list if table["page"] == page]
            page_negs = [negative for negative in neg_by_pdf[pdf_id] if negative["page"] == page]
            predictions = preds_by_page.get(page, [])
            page_pred_totals[page] = len(predictions)
            matched = _match_page(page_gold, predictions)
            matched_pairs.update(matched)
            tp += len(matched)
            fn += len(page_gold) - len(matched)
            total_preds_on_gold_pages += len(predictions)
            for table in page_gold:
                fragment_counts[table["item_id"]] = sum(
                    1 for pred in predictions
                    if _over_pred(pred["bbox"], table["table"]["bbox"]) >= IOU_SCOPE)

            matched_pred_ids = {pred["table_id"] for pred, _ in matched.values()}
            regions = [table["table"]["bbox"] for table in page_gold]
            regions += [negative["bbox"] for negative in page_negs]
            for pred in predictions:
                run_status[pdf_id][pred.get("reconstruction_status", "unknown")] += 1
                if pred["table_id"] in matched_pred_ids:
                    continue
                if any(_over_pred(pred["bbox"], region) >= IOU_SCOPE for region in regions):
                    fp += 1
                    fp_rows.append({
                        "pdf_id": pdf_id,
                        "page": page,
                        "prediction_id": pred["table_id"],
                        "table_type": pred["table_type"],
                        "reconstruction_status": pred.get("reconstruction_status"),
                        "overlap_gold_table": round(max(
                            (_over_pred(pred["bbox"], region) for region in
                             [table["table"]["bbox"] for table in page_gold]), default=0.0), 3),
                        "overlap_negative": round(max(
                            (_over_pred(pred["bbox"], negative["bbox"])
                             for negative in page_negs), default=0.0), 3),
                    })
                else:
                    out_of_scope += 1
            for pred in predictions:
                if pred["table_id"] in matched_pred_ids:
                    continue
                for negative in page_negs:
                    if _over_pred(pred["bbox"], negative["bbox"]) >= IOU_SCOPE:
                        negative_rows.append({
                            "negative_id": negative["item_id"],
                            "negative_kind": negative["negative_kind"],
                            "pdf_id": pdf_id,
                            "page": page,
                            "prediction_id": pred["table_id"],
                            "table_type": pred["table_type"],
                            "reconstruction_status": pred.get("reconstruction_status"),
                            "overlap": round(_over_pred(pred["bbox"], negative["bbox"]), 3),
                        })

        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_out_of_scope += out_of_scope
        scores = _prf(tp, fp, fn)
        per_pdf_rows[pdf_id] = {
            "tables": len(gold_list), "tp": tp, "fp": fp, "fn": fn,
            **scores, "out_of_scope_predictions": out_of_scope,
            "predictions_on_gold_pages": sum(page_pred_totals.values()),
            "negative_items": len(neg_by_pdf[pdf_id]),
        }

        for table in gold_list:
            pair = matched_pairs.get(table["item_id"])
            record = {
                "item_id": table["item_id"],
                "pdf_id": pdf_id,
                "page": table["page"],
                "gold_rows": table["table"]["n_rows"],
                "gold_columns": table["table"]["n_columns"],
                "gold_data_rows": table["table"]["n_data_rows"],
                "gold_table_type": table["table"]["table_type"],
                "cross_page": table["table"].get("cross_page"),
                "overlapping_predictions": fragment_counts.get(table["item_id"], 0),
                "matched": bool(pair),
            }
            if pair:
                pred, score = pair
                record.update({
                    "prediction_id": pred["table_id"],
                    "iou": round(score, 4),
                    "pred_rows": len(pred["rows"]),
                    "pred_columns": _prediction_columns(pred),
                    "pred_table_type": pred["table_type"],
                    "reconstruction_status": pred.get("reconstruction_status"),
                    "structure": _score_pair(table, pred, roles),
                })
            else:
                record.update({
                    "prediction_id": None,
                    "iou": 0.0,
                    "best_iou": round(max(
                        (_iou(table["table"]["bbox"], pred["bbox"])
                         for pred in preds_by_page.get(table["page"], [])), default=0.0), 4),
                })
            details.append(record)

    error_cases = {
        "missed_tables": [{
            "item_id": item["item_id"], "pdf_id": item["pdf_id"], "page": item["page"],
            "gold_rows": item["gold_rows"], "gold_columns": item["gold_columns"],
            "gold_table_type": item["gold_table_type"], "best_iou": item["best_iou"],
        } for item in details if not item["matched"]],
        "in_scope_false_positives": fp_rows,
        "row_count_mismatch": [{
            "item_id": item["item_id"], "pdf_id": item["pdf_id"], "page": item["page"],
            "gold_rows": item["gold_rows"], "pred_rows": item["pred_rows"],
        } for item in details if item["matched"]
            and not item["structure"]["rows"]["exact"]],
        "column_count_mismatch": [{
            "item_id": item["item_id"], "pdf_id": item["pdf_id"], "page": item["page"],
            "gold_columns": item["gold_columns"], "pred_columns": item["pred_columns"],
            "gold_header_rows": item["structure"]["headers"]["gold_rows"],
            "pred_header_rows": item["structure"]["headers"]["pred_rows"],
        } for item in details if item["matched"]
            and not item["structure"]["columns"]["exact"]],
        "header_text_mismatch": [{
            "item_id": item["item_id"], "pdf_id": item["pdf_id"], "page": item["page"],
            "gold_headers": item["structure"]["headers"]["gold_text"],
            "pred_headers": item["structure"]["headers"]["pred_text"],
            "column_hits": item["structure"]["headers"]["column_hits"],
            "columns": item["structure"]["headers"]["columns"],
        } for item in details if item["matched"]
            and item["structure"]["headers"]["comparable"]
            and not item["structure"]["headers"]["all_exact"]],
        "column_role_mismatch": [{
            "item_id": item["item_id"], "pdf_id": item["pdf_id"], "page": item["page"],
            "gold_roles": item["structure"]["roles"]["gold"],
            "pred_roles": item["structure"]["roles"]["pred"],
        } for item in details if item["matched"]
            and not item["structure"]["roles"]["all_exact"]],
    }

    negative_kinds = {}
    for negative in negatives:
        rows = [row for row in negative_rows if row["negative_id"] == negative["item_id"]]
        negative_kinds[negative["item_id"]] = len(rows)
    kind_summary: dict[str, dict] = {}
    for negative in negatives:
        kind = negative["negative_kind"]
        entry = kind_summary.setdefault(kind, {"items": 0, "items_with_fp": 0, "fp": 0})
        entry["items"] += 1
        hits = negative_kinds[negative["item_id"]]
        entry["fp"] += hits
        entry["items_with_fp"] += 1 if hits else 0

    overall = {
        "tables": len(gold_tables), "tp": total_tp, "fp": total_fp, "fn": total_fn,
        **_prf(total_tp, total_fp, total_fn),
        "out_of_scope_predictions": total_out_of_scope,
        "predictions_on_gold_pages": total_preds_on_gold_pages,
        "negative_items": len(negatives),
        "negative_items_with_fp": sum(1 for count in negative_kinds.values() if count),
        "negative_fp": len(negative_rows),
    }

    matched_details = [item for item in details if item["matched"]]
    if matched_details:
        exact_rows = sum(1 for item in matched_details if item["structure"]["rows"]["exact"])
        exact_columns = sum(1 for item in matched_details if item["structure"]["columns"]["exact"])
        count_exact = sum(1 for item in matched_details
                          if item["structure"]["rows"]["exact"]
                          and item["structure"]["columns"]["exact"])
        text_tp = sum(item["structure"]["cells"]["tp"] for item in matched_details)
        text_fp = sum(item["structure"]["cells"]["fp"] for item in matched_details)
        text_fn = sum(item["structure"]["cells"]["fn"] for item in matched_details)
        text_f1 = (2 * text_tp / (2 * text_tp + text_fp + text_fn)
                   if 2 * text_tp + text_fp + text_fn else 0.0)
        comparable = [item for item in matched_details
                      if item["structure"]["headers"]["comparable"]]
        header_hits = sum(item["structure"]["headers"]["column_hits"] for item in comparable)
        header_hits_strict = sum(item["structure"]["headers"]["column_hits_strict"]
                                 for item in comparable)
        header_cols = sum(item["structure"]["headers"]["columns"] for item in comparable)
        headers_exact = sum(1 for item in comparable
                            if item["structure"]["headers"]["all_exact"])
        header_tp = sum(item["structure"]["headers"]["cell_text_tp"] for item in comparable)
        header_fp = sum(item["structure"]["headers"]["cell_text_fp"] for item in comparable)
        header_fn = sum(item["structure"]["headers"]["cell_text_fn"] for item in comparable)
        multi_gold = [item for item in matched_details
                      if item["structure"]["headers"]["gold_rows"] >= 2]
        multi_exact = sum(1 for item in multi_gold
                          if item["structure"]["headers"]["row_depth_exact"])
        header_depth_exact = sum(1 for item in matched_details
                                 if item["structure"]["headers"]["row_depth_exact"])
        header_path_present = sum(1 for item in matched_details
                                  if item["structure"]["headers"]["header_path_present"])
        role_hits = sum(item["structure"]["roles"]["column_hits"] for item in comparable)
        role_cols = sum(item["structure"]["roles"]["columns"] for item in comparable)
        roles_exact = sum(1 for item in matched_details if item["structure"]["roles"]["all_exact"])
        type_hits = sum(1 for item in matched_details if item["structure"]["table_type"]["exact"])
        status_counts = Counter(item["reconstruction_status"] for item in matched_details)
        row_error = Counter(item["structure"]["rows"]["error"] for item in matched_details)
        column_error = Counter(item["structure"]["columns"]["error"] for item in matched_details)
        role_metrics = _role_metrics(matched_details)
        type_confusion = _confusion_matrix(
            [(item["structure"]["table_type"]["gold"], item["structure"]["table_type"]["pred"])
             for item in matched_details],
            ["absolute_maximum", "recommended_operating", "electrical_characteristics",
             "thermal", "pin_functions", "ordering_information", "other", "unknown"])
        header_row_confusion = _confusion_matrix(
            [(str(item["structure"]["headers"]["gold_rows"]),
              str(item["structure"]["headers"]["pred_rows"])) for item in matched_details],
            [str(index) for index in range(5)])
        structure = {
            "matched": len(matched_details),
            "row_count_exact": exact_rows,
            "column_count_exact": exact_columns,
            "row_and_column_exact": count_exact,
            "cell_text_tp": text_tp, "cell_text_fp": text_fp, "cell_text_fn": text_fn,
            "cell_text_f1": round(text_f1, 4),
            "header_column_accuracy": round(header_hits / header_cols, 4) if header_cols else 0.0,
            "header_column_accuracy_strict": (round(header_hits_strict / header_cols, 4)
                                              if header_cols else 0.0),
            "header_tables_exact": headers_exact,
            "header_comparable_tables": len(comparable),
            "header_comparable_columns": header_cols,
            "header_cell_text_tp": header_tp,
            "header_cell_text_fp": header_fp,
            "header_cell_text_fn": header_fn,
            "header_cell_text_f1": round(
                2 * header_tp / (2 * header_tp + header_fp + header_fn)
                if 2 * header_tp + header_fp + header_fn else 0.0, 4),
            "header_multilayer_tables": len(multi_gold),
            "header_multilayer_exact": multi_exact,
            "header_row_depth_exact": header_depth_exact,
            "header_path_tables": header_path_present,
            "column_role_accuracy": round(role_hits / role_cols, 4) if role_cols else 0.0,
            "column_role_columns": role_cols,
            "column_role_tables_exact": roles_exact,
            "column_role_by_role": role_metrics["by_role"],
            "table_type_accuracy": round(type_hits / len(matched_details), 4),
            "reconstruction_status": dict(status_counts),
            "row_error_distribution": {str(key): value for key, value in sorted(row_error.items())},
            "column_error_distribution": {str(key): value for key, value
                                          in sorted(column_error.items())},
            "confusion": {
                "table_type": type_confusion,
                "header_rows": header_row_confusion,
                "column_role": role_metrics["confusion"],
            },
            "denominators": {
                "detection_precision": "TP + in-scope FP (predictions on annotated pages)",
                "detection_recall": "TP + FN (accepted gold tables)",
                "row_count": f"{len(matched_details)} matched tables",
                "column_count": f"{len(matched_details)} matched tables",
                "cell_text": "matched tables; multiset F1 over non-empty cell texts",
                "header_cell_text": f"{len(comparable)} matched tables with equal column count; "
                                    "multiset F1 over non-empty header labels, whitespace-free",
                "header_column_attribution": f"{header_cols} labelled gold header columns "
                                             f"(empty gold labels excluded) in "
                                             f"{len(comparable)} comparable matched tables; "
                                             "strict variant keeps intra-label spacing",
                "header_multilayer": f"{len(multi_gold)} matched gold tables with header_rows >= 2",
                "header_row_detection": "header_rows exact over all matched tables",
                "column_role": f"{role_cols} gold columns in comparable matched tables",
            },
        }
    else:
        structure = {"matched": 0}

    single_row = [item for item in details if item["gold_data_rows"] == 1]
    cross_page = [item for item in details if item["cross_page"]]
    fragments = [item["overlapping_predictions"] for item in details]
    max_fragments = max(fragments) if fragments else 0
    type_counts = Counter(table["table"]["table_type"] for table in gold_tables)
    return {
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "annotation_version": annotation_version,
        "baseline": baseline or {},
        "runs": [{"pdf_id": pdf_id, "run_id": run["run_id"], "run_dir": run["run_dir"],
                  "parser_config_sha256": run["parser_config_sha256"],
                  "parser_version": run["parser_version"]}
                 for pdf_id, run in sorted(used_runs.items())],
        "protocol": {
            "iou_match": IOU_MATCH, "scope_overlap": IOU_SCOPE,
            "scope": "prediction must overlap an annotated table or negative region",
        },
        "overall": overall,
        "per_pdf": per_pdf_rows,
        "gold_composition": {
            "table_types": dict(sorted(type_counts.items())),
            "tables_per_pdf": {pdf_id: len(rows) for pdf_id, rows in sorted(by_pdf.items())},
            "negatives_per_pdf": {pdf_id: len(rows) for pdf_id, rows in sorted(neg_by_pdf.items())},
        },
        "fragmentation": {
            "mean_overlapping_predictions": round(sum(fragments) / len(fragments), 3)
            if fragments else 0.0,
            "max_overlapping_predictions": max_fragments,
            "max_items": [item["item_id"] for item in details
                          if item["overlapping_predictions"] == max_fragments][:10],
            "distribution": {str(key): value
                             for key, value in sorted(Counter(fragments).items())},
        },
        "structure": structure,
        "error_cases": error_cases,
        "single_row_tables": {
            "count": len(single_row),
            "matched": sum(1 for item in single_row if item["matched"]),
            "items": single_row,
        },
        "cross_page_tables": {
            "count": len(cross_page),
            "matched": sum(1 for item in cross_page if item["matched"]),
            "items": cross_page,
        },
        "negatives": {
            "by_kind": kind_summary,
            "by_item": negative_kinds,
            "false_positive_predictions": negative_rows,
        },
        "tables": details,
        "run_status_on_gold_pages": {key: dict(value) for key, value in run_status.items()},
    }


def _fmt(value) -> str:
    return f"{value:.4f}" if isinstance(value, float) else str(value)


def _write_csv(path: Path, details: list[dict]) -> None:
    fields = ["item_id", "pdf_id", "page", "matched", "prediction_id", "iou", "best_iou",
              "gold_rows", "pred_rows", "gold_columns", "pred_columns",
              "gold_data_rows", "overlapping_predictions", "gold_table_type",
              "pred_table_type", "reconstruction_status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in details:
            writer.writerow({key: item.get(key) for key in fields})


def _write_markdown(path: Path, report: dict) -> None:
    overall = report["overall"]
    structure = report["structure"]
    lines = [
        f"# Gold Set evaluation: {report['label']}",
        "",
        f"- Gold annotation: `{report['annotation_version']}`",
        f"- Baseline: `{report['baseline'].get('tag', '-')}` at "
        f"`{report['baseline'].get('commit', '-')}`",
        f"- Generated: {report['generated_at']}",
        f"- Matching: one-to-one per page, IoU >= {report['protocol']['iou_match']}; "
        f"in-scope FP when overlap/prediction >= {report['protocol']['scope_overlap']}",
        f"- Scope: {report['protocol']['scope']}",
        "",
        "## Gold set composition",
        "",
        "| PDF | Tables | Negatives |",
        "| --- | --- | --- |",
    ]
    for pdf_id in sorted(report["gold_composition"]["tables_per_pdf"]):
        lines.append(f"| {pdf_id} | {report['gold_composition']['tables_per_pdf'][pdf_id]} | "
                     f"{report['gold_composition']['negatives_per_pdf'].get(pdf_id, 0)} |")
    lines += [
        "",
        f"Table types: {report['gold_composition']['table_types']}",
        "",
        "## Runs",
        "",
        "| PDF | Run | Parser config SHA256 |",
        "| --- | --- | --- |",
    ]
    for run in report["runs"]:
        lines.append(f"| {run['pdf_id']} | `{run['run_id']}` | `{run['parser_config_sha256']}` |")
    lines += [
        "",
        "## Overall table detection",
        "",
        "| Gold tables | TP | FP | FN | Precision | Recall | F1 | Out-of-scope predictions | Predictions on gold pages |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| {overall['tables']} | {overall['tp']} | {overall['fp']} | {overall['fn']} | "
        f"{overall['precision']:.4f} | {overall['recall']:.4f} | {overall['f1']:.4f} | "
        f"{overall['out_of_scope_predictions']} | {overall['predictions_on_gold_pages']} |",
        "",
        "## Per PDF",
        "",
        "| PDF | Gold | TP | FP | FN | Precision | Recall | F1 | Out-of-scope | Predictions |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for pdf_id, row in report["per_pdf"].items():
        lines.append(
            f"| {pdf_id} | {row['tables']} | {row['tp']} | {row['fp']} | {row['fn']} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | "
            f"{row['out_of_scope_predictions']} | {row['predictions_on_gold_pages']} |")
    lines += [
        "",
        "## Over-detection / fragmentation",
        "",
        f"- Predictions on gold pages: {overall['predictions_on_gold_pages']}",
        f"- In-scope false positives: {overall['fp']}",
        f"- Out-of-scope predictions (unannotated page area): {overall['out_of_scope_predictions']}",
        f"- Mean predictions overlapping one gold table: "
        f"{report['fragmentation']['mean_overlapping_predictions']}",
        f"- Maximum predictions overlapping one gold table: "
        f"{report['fragmentation']['max_overlapping_predictions']} "
        f"({', '.join(report['fragmentation']['max_items'])})",
        f"- Overlap-count distribution: {report['fragmentation']['distribution']}",
        "",
        "## Structure on matched tables",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Matched tables | {structure['matched']} |",
        f"| Row count exact | {structure.get('row_count_exact', 0)} |",
        f"| Column count exact | {structure.get('column_count_exact', 0)} |",
        f"| Row and column exact | {structure.get('row_and_column_exact', 0)} |",
        f"| Cell-text F1 | {structure.get('cell_text_f1', 0.0):.4f} |",
        f"| Header column accuracy | {structure.get('header_column_accuracy', 0.0):.4f} |",
        f"| Header column accuracy (strict spacing) | "
        f"{structure.get('header_column_accuracy_strict', 0.0):.4f} |",
        f"| Header row-depth exact | {structure.get('header_row_depth_exact', 0)} | "
        f"(of {structure.get('matched', 0)} matched) |",
        f"| Header tables exact | {structure.get('header_tables_exact', 0)} | "
        f"(of {structure.get('header_comparable_tables', 0)} comparable) |",
        f"| Header cell-text F1 | {structure.get('header_cell_text_f1', 0.0):.4f} |",
        f"| Multi-layer header exact | {structure.get('header_multilayer_exact', 0)} | "
        f"(of {structure.get('header_multilayer_tables', 0)}) |",
        f"| Tables carrying header_path | {structure.get('header_path_tables', 0)} |",
        f"| Column-role accuracy | {structure.get('column_role_accuracy', 0.0):.4f} |",
        f"| Column-role tables exact | {structure.get('column_role_tables_exact', 0)} |",
        f"| Table-type accuracy | {structure.get('table_type_accuracy', 0.0):.4f} |",
        f"| Reconstruction status (matched) | {structure.get('reconstruction_status', {})} |",
        f"| Row error distribution | {structure.get('row_error_distribution', {})} |",
        f"| Column error distribution | {structure.get('column_error_distribution', {})} |",
        "",
        "## Metric denominators",
        "",
        "| Metric family | Denominator |",
        "| --- | --- |",
    ]
    for family, denominator in structure.get("denominators", {}).items():
        lines.append(f"| {family} | {denominator} |")
    lines += [
        "",
        "## Column roles by role",
        "",
        "| Role | Gold columns | Predicted columns | TP | FP | FN | Precision | Recall | F1 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for role, row in structure.get("column_role_by_role", {}).items():
        lines.append(f"| {role} | {row['gold']} | {row['pred']} | {row['tp']} | {row['fp']} | "
                     f"{row['fn']} | {row['precision']:.4f} | {row['recall']:.4f} | "
                     f"{row['f1']:.4f} |")
    lines += ["", "## Confusion matrices", ""]
    for title, matrix in (structure.get("confusion") or {}).items():
        if not matrix:
            continue
        columns = list(next(iter(matrix.values())).keys())
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| gold \\ pred | " + " | ".join(columns) + " |")
        lines.append("| --- | " + " | ".join("---" for _ in columns) + " |")
        for gold, row in matrix.items():
            lines.append(f"| {gold} | " + " | ".join(str(row.get(column, 0))
                                                     for column in columns) + " |")
        lines.append("")
    lines += [
        "## Error cases",
        "",
        f"- Missed tables (FN): {len(report['error_cases']['missed_tables'])}",
        f"- In-scope false positives: {len(report['error_cases']['in_scope_false_positives'])}",
        f"- Row-count mismatches: {len(report['error_cases']['row_count_mismatch'])}",
        f"- Column-count mismatches: {len(report['error_cases']['column_count_mismatch'])}",
        f"- Header-text mismatches: {len(report['error_cases']['header_text_mismatch'])}",
        f"- Column-role mismatches: {len(report['error_cases']['column_role_mismatch'])}",
        "",
        "| Case | Item | Page | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["error_cases"]["missed_tables"]:
        lines.append(f"| FN | {item['item_id']} | {item['page']} | "
                     f"gold {item['gold_rows']} x {item['gold_columns']}, "
                     f"best IoU {item['best_iou']:.4f} |")
    for item in report["error_cases"]["in_scope_false_positives"]:
        lines.append(f"| FP | {item['prediction_id']} | {item['page']} | "
                     f"table overlap {item['overlap_gold_table']:.3f}, "
                     f"negative overlap {item['overlap_negative']:.3f} |")
    for item in report["error_cases"]["row_count_mismatch"]:
        lines.append(f"| rows | {item['item_id']} | {item['page']} | "
                     f"gold {item['gold_rows']} -> pred {item['pred_rows']} |")
    for item in report["error_cases"]["column_count_mismatch"]:
        lines.append(f"| cols | {item['item_id']} | {item['page']} | "
                     f"gold {item['gold_columns']} -> pred {item['pred_columns']} "
                     f"(header rows {item['gold_header_rows']} -> "
                     f"{item['pred_header_rows']}) |")
    for item in report["error_cases"]["header_text_mismatch"]:
        lines.append(f"| headers | {item['item_id']} | {item['page']} | "
                     f"{item['column_hits']}/{item['columns']} column labels match |")
    for item in report["error_cases"]["column_role_mismatch"]:
        lines.append(f"| roles | {item['item_id']} | {item['page']} | "
                     f"gold {item['gold_roles']} -> pred {item['pred_roles']} |")
    lines += [
        "",
        "## Single-row gold tables (must not be dropped)",
        "",
        f"- Gold single-row tables: {report['single_row_tables']['count']}",
        f"- Matched: {report['single_row_tables']['matched']}",
        "",
        "| Item | Matched | Prediction | Status |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["single_row_tables"]["items"]:
        lines.append(f"| {item['item_id']} | {item['matched']} | "
                     f"{item.get('prediction_id') or '-'} | "
                     f"{item.get('reconstruction_status') or '-'} |")
    lines += [
        "",
        "## Cross-page tables",
        "",
        f"- Gold fragments: {report['cross_page_tables']['count']}",
        f"- Matched: {report['cross_page_tables']['matched']}",
        "",
        "## Negative samples",
        "",
        "| Kind | Items | Items with FP | FP predictions |",
        "| --- | --- | --- | --- |",
    ]
    for kind, row in sorted(report["negatives"]["by_kind"].items()):
        lines.append(f"| {kind} | {row['items']} | {row['items_with_fp']} | {row['fp']} |")
    lines += [
        f"| **total** | **{overall['negative_items']}** | "
        f"**{overall['negative_items_with_fp']}** | **{overall['negative_fp']}** |",
        "",
        "## Missed gold tables (FN)",
        "",
        "| Item | Page | Gold rows x cols | Best IoU |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["tables"]:
        if not item["matched"]:
            lines.append(f"| {item['item_id']} | {item['page']} | "
                         f"{item['gold_rows']} x {item['gold_columns']} | {item['best_iou']:.4f} |")
    lines += [
        "",
        "## Matched but structurally wrong",
        "",
        "| Item | IoU | Gold rows x cols | Pred rows x cols | Row/col exact | Type | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["tables"]:
        if not item["matched"]:
            continue
        structure_row = item["structure"]
        if structure_row["rows"]["exact"] and structure_row["columns"]["exact"]:
            continue
        lines.append(
            f"| {item['item_id']} | {item['iou']:.4f} | "
            f"{item['gold_rows']} x {item['gold_columns']} | "
            f"{item['pred_rows']} x {item['pred_columns']} | "
            f"{structure_row['rows']['exact']}/{structure_row['columns']['exact']} | "
            f"{item['gold_table_type']} -> {item['pred_table_type']} | "
            f"{item.get('reconstruction_status')} |")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=ROOT / "gold" / "gold_table_set.jsonl")
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--label", default="baseline-1d8c722")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--csv", type=Path, default=None)
    args = parser.parse_args()

    gold_tables, negatives, gold_meta = _load_gold(args.gold)
    runs = [_load_run(run) for run in args.run]
    if gold_meta["excluded"]:
        print(f"excluded {len(gold_meta['excluded'])} non-accepted items: {gold_meta['excluded']}")
    baseline = {}
    manifest_path = args.gold.parent / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        baseline = {
            "tag": manifest.get("baseline_tag"),
            "commit": manifest.get("baseline_commit"),
            "annotation_version": manifest.get("annotation_version"),
            "pdf_sha256": {key: meta["sha256"] for key, meta in manifest.get("pdfs", {}).items()},
        }
    report = evaluate(gold_tables, negatives, runs, args.label,
                      baseline.get("annotation_version") or "unknown", baseline)
    report["gold_counts"] = {"tables": len(gold_tables), "negatives": len(negatives),
                             "excluded": gold_meta["excluded"]}

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        _write_markdown(args.out, report)
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        _write_csv(args.csv, report["tables"])

    overall = report["overall"]
    print(json.dumps({
        "label": report["label"], "tables": overall["tables"], "tp": overall["tp"],
        "fp": overall["fp"], "fn": overall["fn"], "precision": overall["precision"],
        "recall": overall["recall"], "f1": overall["f1"],
        "negative_fp": overall["negative_fp"],
        "out_of_scope_predictions": overall["out_of_scope_predictions"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
