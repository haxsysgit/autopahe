#!/usr/bin/env python3
import argparse
from manager import (
    load_database, print_all_records, search_record, delete_record,
    update_progress, rate_record, rename_title, set_keyword,
    list_by_status, export_records, import_records,
)

def main():
    parser = argparse.ArgumentParser(prog="manage.py", description="AutoPahe records manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("view", help="Print all records")

    sp = sub.add_parser("search", help="Search records by keyword or title")
    sp.add_argument("query")

    sp = sub.add_parser("delete", help="Delete a record by index or exact title")
    sp.add_argument("id_or_title")

    sp = sub.add_parser("progress", help="Update current episode progress")
    sp.add_argument("id_or_title")
    sp.add_argument("episode", type=int)

    sp = sub.add_parser("rate", help="Rate an anime (0-10)")
    sp.add_argument("id_or_title")
    sp.add_argument("rating", type=float)

    sp = sub.add_parser("rename", help="Rename a record title")
    sp.add_argument("id_or_title")
    sp.add_argument("new_title")

    sp = sub.add_parser("set-keyword", help="Set or update the keyword for a record")
    sp.add_argument("id_or_title")
    sp.add_argument("keyword")

    sp = sub.add_parser("list-status", help="List records matching a status substring (e.g., completed, watching)")
    sp.add_argument("status")

    sp = sub.add_parser("export", help="Export records to a file (json or csv)")
    sp.add_argument("path")
    sp.add_argument("--fmt", default="json", choices=["json", "csv"])

    sp = sub.add_parser("import", help="Import records from a JSON file (merges with existing)")
    sp.add_argument("path")

    args = parser.parse_args()
    cmd = args.cmd

    if cmd == "view":
        print_all_records()
    elif cmd == "search":
        print(search_record(args.query))
    elif cmd == "delete":
        delete_record(args.id_or_title)
    elif cmd == "progress":
        update_progress(args.id_or_title, args.episode)
    elif cmd == "rate":
        rate_record(args.id_or_title, args.rating)
    elif cmd == "rename":
        rename_title(args.id_or_title, args.new_title)
    elif cmd == "set-keyword":
        set_keyword(args.id_or_title, args.keyword)
    elif cmd == "list-status":
        list_by_status(args.status)
    elif cmd == "export":
        export_records(args.path, args.fmt)
    elif cmd == "import":
        import_records(args.path)

if __name__ == "__main__":
    main()
