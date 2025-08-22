#!/usr/bin/env python3
"""
Interactive chatbot example using chi_llm.
"""

from chi_llm import MicroLLM


def main():
    """Run interactive chatbot."""
    print("🤖 chi_llm Chatbot")
    print("=" * 50)
    print("Type 'quit', 'exit', or 'bye' to end the conversation")
    print("Type 'clear' to clear conversation history")
    print("=" * 50)
    print()

    # Initialize the model
    print("Loading model (first time may take a moment)...")
    llm = MicroLLM(temperature=0.7)
    print("Ready! Let's chat.\n")

    # Conversation history
    history = []

    while True:
        # Get user input
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "bye", "q"]:
            print("\nGoodbye! Thanks for chatting! 👋")
            break

        # Clear history command
        if user_input.lower() == "clear":
            history = []
            print("\n✨ Conversation history cleared!\n")
            continue

        # Skip empty input
        if not user_input:
            continue

        # Generate response
        try:
            response = llm.chat(user_input, history=history)
            print(f"\nAI: {response}\n")

            # Add to history
            history.append({"user": user_input, "assistant": response})

            # Keep history manageable (last 10 exchanges)
            if len(history) > 10:
                history = history[-10:]

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
