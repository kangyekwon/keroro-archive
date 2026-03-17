"""Keroro Archive - CLI Entry Point"""
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Keroro Archive - 케로로 군조 종합 아카이브"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start web server")
    serve_parser.add_argument("--host", default=None, help="Server host")
    serve_parser.add_argument("--port", type=int, default=None, help="Server port")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # search
    search_parser = subparsers.add_parser("search", help="Search the archive")
    search_parser.add_argument("query", help="Search query")

    # character
    char_parser = subparsers.add_parser("character", help="Character lookup")
    char_parser.add_argument("name", nargs="?", help="Character name")
    char_parser.add_argument("--list", action="store_true", help="List all characters")

    # status
    subparsers.add_parser("status", help="Show database statistics")

    args = parser.parse_args()

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "character":
        cmd_character(args)
    elif args.command == "status":
        cmd_status()
    else:
        parser.print_help()


def cmd_serve(args):
    import uvicorn
    from config import SERVER_HOST, SERVER_PORT

    host = args.host or SERVER_HOST
    port = args.port or SERVER_PORT
    print(f"Starting Keroro Archive server at http://{host}:{port}")
    uvicorn.run("api.server:app", host=host, port=port, reload=args.reload)


def cmd_search(args):
    from db.database import Database
    from search.engine import SearchEngine

    db = Database()
    engine = SearchEngine(db)
    results = engine.search_all(args.query)

    total = sum(len(v) for v in results.values())
    print(f"\n'{args.query}' 검색 결과: {total}건\n")

    for category, items in results.items():
        if items:
            print(f"[{category}] {len(items)}건")
            for item in items[:5]:
                name = item.get("name") or item.get("title") or item.get("content", "")
                print(f"  - {name}")
            if len(items) > 5:
                print(f"  ... 외 {len(items) - 5}건")
            print()

    db.close()


def cmd_character(args):
    from db.database import Database

    db = Database()

    if args.list or not args.name:
        rows = db.fetchall("SELECT id, name, name_kr, race, platoon FROM characters ORDER BY id")
        print(f"\n전체 캐릭터 목록 ({len(rows)}명)\n")
        for row in rows:
            r = dict(row)
            platoon = f" [{r['platoon']}]" if r.get("platoon") else ""
            print(f"  {r['id']:3d}. {r['name_kr'] or r['name']}{platoon} ({r['race']})")
    else:
        row = db.fetchone(
            "SELECT * FROM characters WHERE name LIKE ? OR name_kr LIKE ?",
            (f"%{args.name}%", f"%{args.name}%"),
        )
        if row:
            r = dict(row)
            print(f"\n{'=' * 40}")
            print(f"  {r['name_kr']} ({r['name']})")
            print(f"  종족: {r['race']}")
            if r.get("platoon"):
                print(f"  소속: {r['platoon']}")
            if r.get("rank"):
                print(f"  계급: {r['rank']}")
            if r.get("description"):
                print(f"  설명: {r['description'][:100]}")
            print(f"{'=' * 40}\n")
        else:
            print(f"'{args.name}' 캐릭터를 찾을 수 없습니다.")

    db.close()


def cmd_status():
    from db.database import Database
    from search.engine import SearchEngine

    db = Database()
    engine = SearchEngine(db)
    stats = engine.get_stats()

    print("\n=== Keroro Archive Status ===\n")
    for table, count in stats.items():
        print(f"  {table}: {count}건")
    print()

    db.close()


if __name__ == "__main__":
    main()
