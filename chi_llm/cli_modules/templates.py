"""
Prompt templates command.
"""

import sys
from argparse import _SubParsersAction
from ..core import MicroLLM
from ..prompts import PromptTemplates


def cmd_template(args):
    llm = MicroLLM()
    templates = PromptTemplates()
    template_map = {
        "code-review": lambda: templates.code_review(
            args.input, language=args.language
        ),
        "explain-code": lambda: templates.explain_code(args.input),
        "fix-error": lambda: templates.fix_error(args.input, args.error),
        "write-tests": lambda: templates.write_tests(
            args.input, framework=args.framework
        ),
        "optimize": lambda: templates.optimize_code(args.input),
        "document": lambda: templates.document_code(args.input, style=args.style),
        "sql": lambda: templates.sql_from_description(args.input),
        "regex": lambda: templates.regex_from_description(args.input),
        "email": lambda: templates.email_draft(args.input, tone=args.tone),
        "commit": lambda: templates.commit_message(args.input),
        "user-story": lambda: templates.user_story(args.input),
    }
    if args.template not in template_map:
        print(f"❌ Unknown template: {args.template}")
        print(f"Available templates: {', '.join(template_map.keys())}")
        sys.exit(1)
    if args.file:
        with open(args.file, "r") as f:
            args.input = f.read()
    prompt = template_map[args.template]()
    response = llm.generate(prompt)
    print(response)


def register(subparsers: _SubParsersAction):
    tmpl_parser = subparsers.add_parser("template", help="Use prompt templates")
    tmpl_parser.add_argument(
        "template",
        choices=[
            "code-review",
            "explain-code",
            "fix-error",
            "write-tests",
            "optimize",
            "document",
            "sql",
            "regex",
            "email",
            "commit",
            "user-story",
        ],
        help="Template to use",
    )
    tmpl_parser.add_argument("input", nargs="?", help="Input text")
    tmpl_parser.add_argument("-f", "--file", help="Read input from file")
    tmpl_parser.add_argument("--language", help="Programming language")
    tmpl_parser.add_argument("--error", help="Error message (for fix-error)")
    tmpl_parser.add_argument("--framework", default="pytest", help="Test framework")
    tmpl_parser.add_argument("--style", default="google", help="Doc style")
    tmpl_parser.add_argument("--tone", default="professional", help="Email tone")
    tmpl_parser.set_defaults(func=cmd_template)
