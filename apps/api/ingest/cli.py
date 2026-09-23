"""Command line entry for textbook ingest and unit lookup."""

import argparse
import sys
from pathlib import Path

from bangxue_env import load_repo_env

load_repo_env()

from ingest.embed import embed_texts, embedding_dimension
from ingest.parse import extract_pages
from ingest.split import UnitSplitError, split_pages
from ingest.store import connect, count_book, fetch_unit, replace_book


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "ingest":
        return _ingest(args)
    if args.command == "query":
        return _query(args)
    parser.print_help()
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingest",
        description="Ingest one textbook PDF into pgvector, or look up one unit.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Parse, split, and store one textbook")
    _add_meta(ingest)
    ingest.add_argument("--pdf", required=True, type=Path, help="Path to one textbook PDF")
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
    pdf_path = args.pdf.expanduser().resolve()
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1
    pages = extract_pages(pdf_path)
    try:
        chunks = split_pages(pages)
    except UnitSplitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    meta = {
        "stage": args.stage,
        "grade": args.grade,
        "subject": args.subject,
        "edition": args.edition,
        "term": args.term,
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
    print(f"Stored {inserted} chunks (rows for this book: {stored}).")
    return 0


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
