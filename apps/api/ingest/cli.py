"""Command line entry for textbook ingest and unit lookup."""

import argparse
import sys
from pathlib import Path

from bangxue_env import load_repo_env

load_repo_env()

from ingest.catalog import (
    BookTarget,
    default_primary_math_root,
    discover_primary_math_pdfs,
    parse_primary_math_meta,
)
from ingest.embed import embed_texts, embedding_dimension
from ingest.parse import extract_pages
from ingest.split import UnitSplitError, split_pages
from ingest.store import connect, count_book, fetch_unit, replace_book


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "ingest":
        return _ingest(args)
    if args.command == "ingest-primary-math":
        return _ingest_primary_math(args)
    if args.command == "query":
        return _query(args)
    parser.print_help()
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingest",
        description="Ingest textbook PDFs into pgvector, or look up one unit.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Parse, split, and store one textbook")
    _add_meta(ingest)
    ingest.add_argument("--pdf", required=True, type=Path, help="Path to one textbook PDF")
    batch = sub.add_parser(
        "ingest-primary-math",
        help="Ingest every primary-math PDF under book/小学/数学",
    )
    batch.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Override book/小学/数学 root (default: repo book/小学/数学)",
    )
    query = sub.add_parser("query", help="Fetch stored chunks for one unit")
    _add_meta(query)
    query.add_argument("--unit", required=True, help="Unit name stored with the chunks")
    return parser


def _add_meta(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--stage", required=True, help="School stage, e.g. 小学")
    parser.add_argument("--grade", required=True, help="Grade, e.g. 一年级")
    parser.add_argument("--subject", required=True, help="Subject, e.g. 数学")
    parser.add_argument("--edition", required=True, help="Textbook edition, e.g. 人教版")
    parser.add_argument("--term", required=True, help="Term, e.g. 上册")


def _ingest(args: argparse.Namespace) -> int:
    target = BookTarget(
        pdf=args.pdf.expanduser().resolve(),
        stage=args.stage,
        grade=args.grade,
        subject=args.subject,
        edition=args.edition,
        term=args.term,
    )
    try:
        inserted, stored = _ingest_one(target)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UnitSplitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Stored {inserted} chunks (rows for this book: {stored}).")
    return 0


def _ingest_primary_math(args: argparse.Namespace) -> int:
    root = (args.root or default_primary_math_root()).expanduser().resolve()
    pdfs = discover_primary_math_pdfs(root)
    if not pdfs:
        print(f"No PDFs under {root}", file=sys.stderr)
        return 1
    ok = 0
    failed: list[tuple[str, str]] = []
    for pdf in pdfs:
        try:
            target = parse_primary_math_meta(pdf)
        except ValueError as exc:
            failed.append((pdf.name, str(exc)))
            print(f"SKIP {pdf.name}: {exc}", file=sys.stderr)
            continue
        print(
            f"INGEST {target.grade}{target.term} ({pdf.name}) …",
            flush=True,
        )
        try:
            inserted, stored = _ingest_one(target)
        except Exception as exc:  # noqa: BLE001 - batch continues after one book fails
            failed.append((pdf.name, str(exc)))
            print(f"FAIL {pdf.name}: {exc}", file=sys.stderr)
            continue
        ok += 1
        print(f"OK {target.grade}{target.term}: {inserted} chunks ({stored} rows).")
    print(f"Done. success={ok} failed={len(failed)} total={len(pdfs)}")
    for name, reason in failed:
        print(f"  failed: {name} — {reason}")
    return 0 if ok else 1


def _ingest_one(target: BookTarget) -> tuple[int, int]:
    pdf_path = target.pdf.expanduser().resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    pages = extract_pages(pdf_path)
    chunks = split_pages(pages)
    meta = {
        "stage": target.stage,
        "grade": target.grade,
        "subject": target.subject,
        "edition": target.edition,
        "term": target.term,
    }
    with connect() as conn:
        inserted = replace_book(
            conn,
            chunks=chunks,
            embedder=embed_texts,
            dimension=embedding_dimension(),
            **meta,
        )
        stored = count_book(conn, **meta)
    return inserted, stored


def _query(args: argparse.Namespace) -> int:
    with connect() as conn:
        rows = fetch_unit(
            conn,
            stage=args.stage,
            grade=args.grade,
            subject=args.subject,
            edition=args.edition,
            term=args.term,
            unit_name=args.unit,
        )
    if not rows:
        print("No chunks for that unit.", file=sys.stderr)
        return 1
    for unit_name, page_start, page_end, content in rows:
        preview = content.replace("\n", " ")[:80]
        print(f"{unit_name}\t{page_start}-{page_end}\t{preview}")
    return 0
