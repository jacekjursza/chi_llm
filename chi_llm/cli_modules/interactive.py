"""
Interactive shell command.
"""

from argparse import _SubParsersAction
from ..core import MicroLLM


def cmd_interactive(args):
    print("🤖 Chi_LLM Interactive Mode")
    print("Type 'help' for available commands, 'exit' to quit")
    print("-" * 60)
    llm = MicroLLM()
    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 Goodbye!")
                break
            if user_input.lower() == "help":
                print(
                    """
Available commands:
  chat          - Start chat conversation
  generate TEXT - Generate text
  complete TEXT - Complete text
  ask QUESTION  - Ask a question
  summarize TEXT - Summarize text
  translate TEXT - Translate to English
  help          - Show this help
  exit          - Exit interactive mode
                    """
                )
                continue
            parts = user_input.split(" ", 1)
            command = parts[0].lower()
            text = parts[1] if len(parts) > 1 else ""
            if command == "chat":
                print("Starting chat mode (type 'back' to return)...")
                chat_history = []
                while True:
                    chat_input = input("You: ").strip()
                    if chat_input.lower() == "back":
                        break
                    response = llm.chat(chat_input, history=chat_history)
                    print(f"AI: {response}")
                    chat_history.append({"user": chat_input, "assistant": response})
            elif command == "generate":
                print(llm.generate(text))
            elif command == "complete":
                print(llm.complete(text))
            elif command == "ask":
                print(llm.ask(text))
            elif command == "summarize":
                print(llm.summarize(text, max_sentences=3))
            elif command == "translate":
                print(llm.translate(text, target_language="English"))
            else:
                print(llm.generate(user_input))
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def register(subparsers: _SubParsersAction):
    inter_parser = subparsers.add_parser("interactive", help="Interactive mode")
    inter_parser.set_defaults(func=cmd_interactive)
