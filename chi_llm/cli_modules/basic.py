"""
Basic text and chat commands.
"""

import sys
from pathlib import Path
from argparse import _SubParsersAction

from ..core import MicroLLM
from ..analyzer import CodeAnalyzer, DEFAULT_QUESTION


def cmd_generate(args):
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    if args.file:
        with open(args.file, "r") as f:
            prompt = f.read()
    else:
        prompt = args.prompt
    response = llm.generate(prompt)
    print(response)


def cmd_chat(args):
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    history = []
    print("🤖 Chi_LLM Chat (type 'exit' or 'quit' to stop)")
    print("-" * 60)
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n👋 Goodbye!")
                break
            if not user_input:
                continue
            print("\nAI: ", end="", flush=True)
            response = llm.chat(user_input, history=history)
            print(response)
            history.append({"user": user_input, "assistant": response})
            if len(history) > 10:
                history = history[-10:]
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def cmd_complete(args):
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.text
    response = llm.complete(text)
    print(response)


def cmd_ask(args):
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    context = None
    if args.context_file:
        with open(args.context_file, "r") as f:
            context = f.read()
    elif args.context:
        context = args.context
    response = llm.ask(args.question, context=context)
    print(response)


def cmd_analyze(args):
    # Optional GPU override
    if args.no_gpu:
        import os

        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    try:
        analyzer = CodeAnalyzer(use_gpu=not args.no_gpu)
        print(f"📄 Analyzing: {Path(args.file_path).name}")
        print(f"❓ Question: {args.question}\n")
        print("-" * 60)
        response = analyzer.analyze_file(args.file_path, args.question)
        print("\n💡 Analysis Result:")
        print("-" * 60)
        print(response)
        print("-" * 60)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def register(subparsers: _SubParsersAction):
    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate text from prompt")
    gen_parser.add_argument("prompt", nargs="?", help="Text prompt")
    gen_parser.add_argument("-f", "--file", help="Read prompt from file")
    gen_parser.add_argument(
        "-t", "--temperature", type=float, default=0.7, help="Temperature (0.0-1.0)"
    )
    gen_parser.add_argument(
        "-m", "--max-tokens", type=int, default=4096, help="Max tokens"
    )
    gen_parser.set_defaults(func=cmd_generate)

    # chat
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")
    chat_parser.add_argument(
        "-t", "--temperature", type=float, default=0.7, help="Temperature"
    )
    chat_parser.add_argument(
        "-m", "--max-tokens", type=int, default=4096, help="Max tokens"
    )
    chat_parser.set_defaults(func=cmd_chat)

    # complete
    comp_parser = subparsers.add_parser("complete", help="Complete/continue text")
    comp_parser.add_argument("text", nargs="?", help="Text to complete")
    comp_parser.add_argument("-f", "--file", help="Read text from file")
    comp_parser.add_argument(
        "-t", "--temperature", type=float, default=0.7, help="Temperature"
    )
    comp_parser.add_argument(
        "-m", "--max-tokens", type=int, default=4096, help="Max tokens"
    )
    comp_parser.set_defaults(func=cmd_complete)

    # ask
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("question", help="Question to ask")
    ask_parser.add_argument("-c", "--context", help="Context for the question")
    ask_parser.add_argument("-cf", "--context-file", help="Read context from file")
    ask_parser.add_argument(
        "-t", "--temperature", type=float, default=0.7, help="Temperature"
    )
    ask_parser.add_argument(
        "-m", "--max-tokens", type=int, default=4096, help="Max tokens"
    )
    ask_parser.set_defaults(func=cmd_ask)

    # analyze (compat)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code file")
    analyze_parser.add_argument("file_path", help="Path to code file")
    analyze_parser.add_argument(
        "-q", "--question", default=DEFAULT_QUESTION, help="Question about code"
    )
    analyze_parser.add_argument("--no-gpu", action="store_true", help="Force CPU mode")
    analyze_parser.set_defaults(func=cmd_analyze)
