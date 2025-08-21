"""
RAG-related CLI subcommands.
"""

import sys
from argparse import _SubParsersAction

try:
    from ..rag import MicroRAG, quick_rag

    HAS_RAG = True
except Exception:  # pragma: no cover - optional
    HAS_RAG = False


def _ensure_rag():
    if not HAS_RAG:
        print("❌ RAG features not installed. Install with: pip install chi-llm[rag]")
        sys.exit(1)


def cmd_rag(args):
    _ensure_rag()
    if args.rag_command == "query":
        if args.documents:
            docs = []
            for doc_file in args.documents:
                with open(doc_file, "r") as f:
                    docs.append(f.read())
            answer = quick_rag(args.question, docs)
            print(answer)
        elif args.db:
            rag = MicroRAG(db_path=args.db)
            result = rag.query(args.question, include_sources=args.sources)
            if args.sources:
                print(f"Answer: {result['answer']}")
                print(f"\nSources ({len(result['sources'])}):")
                for i, source in enumerate(result["sources"], 1):
                    print(f"  {i}. {source['content'][:100]}...")
            else:
                print(result)
            rag.close()
        elif args.config:
            rag = MicroRAG.from_config(args.config)
            answer = rag.query(args.question)
            print(answer)
            rag.close()
        else:
            print("❌ Provide --documents, --db, or --config")
            sys.exit(1)
    elif args.rag_command == "add":
        if not args.db:
            print("❌ Specify database with --db")
            sys.exit(1)
        rag = MicroRAG(db_path=args.db)
        for doc_file in args.documents:
            with open(doc_file, "r") as f:
                content = f.read()
                doc_id = rag.add_document(content)
                print(f"✅ Added document: {doc_file} (ID: {doc_id})")
        print(f"Total documents: {rag.count_documents()}")
        rag.close()
    elif args.rag_command == "search":
        if not args.db:
            print("❌ Specify database with --db")
            sys.exit(1)
        rag = MicroRAG(db_path=args.db)
        results = rag.search(args.query, top_k=args.top_k)
        print(f"Found {len(results)} results:")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc.content[:200]}...")
            if doc.metadata:
                print(f"   Metadata: {doc.metadata}")
        rag.close()
    elif args.rag_command == "info":
        if not args.db:
            print("❌ Specify database with --db")
            sys.exit(1)
        rag = MicroRAG(db_path=args.db)
        count = rag.count_documents()
        print(f"📚 Database: {args.db}")
        print(f"📄 Documents: {count}")
        rag.close()


def register(subparsers: _SubParsersAction):
    if not HAS_RAG:
        return
    rag_parser = subparsers.add_parser("rag", help="RAG operations")
    rag_sub = rag_parser.add_subparsers(dest="rag_command", help="RAG commands")

    # query
    rag_query = rag_sub.add_parser("query", help="Query documents")
    rag_query.add_argument("question", help="Question to ask")
    rag_query.add_argument("-d", "--documents", nargs="+", help="Document files")
    rag_query.add_argument("--db", help="Database path")
    rag_query.add_argument("--config", help="Config file")
    rag_query.add_argument(
        "-s", "--sources", action="store_true", help="Include sources"
    )

    # add
    rag_add = rag_sub.add_parser("add", help="Add documents to database")
    rag_add.add_argument("documents", nargs="+", help="Document files to add")
    rag_add.add_argument("--db", required=True, help="Database path")

    # search
    rag_search = rag_sub.add_parser("search", help="Search documents")
    rag_search.add_argument("query", help="Search query")
    rag_search.add_argument("--db", required=True, help="Database path")
    rag_search.add_argument(
        "-k", "--top-k", type=int, default=3, help="Number of results"
    )

    # info
    rag_info = rag_sub.add_parser("info", help="Database info")
    rag_info.add_argument("--db", required=True, help="Database path")

    rag_parser.set_defaults(func=cmd_rag)
