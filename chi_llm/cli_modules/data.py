"""
Data-centric commands: extract, summarize, translate, classify.
"""

import json
from argparse import _SubParsersAction
from ..core import MicroLLM


def cmd_extract(args):
    llm = MicroLLM()
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text
    schema = json.loads(args.schema) if args.schema else None
    response = llm.extract(text, format=args.format, schema=schema)
    if args.output:
        with open(args.output, "w") as f:
            f.write(response)
        print(f"✅ Extracted data saved to {args.output}")
    else:
        print(response)


def cmd_summarize(args):
    llm = MicroLLM()
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text
    response = llm.summarize(text, max_sentences=args.sentences)
    print(response)


def cmd_translate(args):
    llm = MicroLLM()
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text
    response = llm.translate(text, target_language=args.language)
    print(response)


def cmd_classify(args):
    llm = MicroLLM()
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text
    categories = args.categories.split(",")
    response = llm.classify(text, categories=categories)
    print(f"Classification: {response}")


def register(subparsers: _SubParsersAction):
    # extract
    extract_parser = subparsers.add_parser("extract", help="Extract structured data")
    extract_parser.add_argument("text", nargs="?", help="Text to extract from")
    extract_parser.add_argument("-f", "--file", help="Read text from file")
    extract_parser.add_argument(
        "--format", default="json", choices=["json", "yaml"], help="Output format"
    )
    extract_parser.add_argument("--schema", help="JSON schema for extraction")
    extract_parser.add_argument("-o", "--output", help="Save to file")
    extract_parser.set_defaults(func=cmd_extract)

    # summarize
    sum_parser = subparsers.add_parser("summarize", help="Summarize text")
    sum_parser.add_argument("text", nargs="?", help="Text to summarize")
    sum_parser.add_argument("-f", "--file", help="Read text from file")
    sum_parser.add_argument(
        "-s", "--sentences", type=int, default=3, help="Max sentences"
    )
    sum_parser.set_defaults(func=cmd_summarize)

    # translate
    trans_parser = subparsers.add_parser("translate", help="Translate text")
    trans_parser.add_argument("text", nargs="?", help="Text to translate")
    trans_parser.add_argument("-f", "--file", help="Read text from file")
    trans_parser.add_argument(
        "-l", "--language", default="English", help="Target language"
    )
    trans_parser.set_defaults(func=cmd_translate)

    # classify
    class_parser = subparsers.add_parser("classify", help="Classify text")
    class_parser.add_argument("text", nargs="?", help="Text to classify")
    class_parser.add_argument("-f", "--file", help="Read text from file")
    class_parser.add_argument(
        "-c", "--categories", required=True, help="Comma-separated categories"
    )
    class_parser.set_defaults(func=cmd_classify)
