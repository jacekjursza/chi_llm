"""
Enhanced CLI for chi_llm - Zero Configuration Micro-LLM Library.
"""

import argparse
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Optional

from .core import MicroLLM, quick_llm
from .analyzer import CodeAnalyzer, DEFAULT_QUESTION
from .prompts import PromptTemplates

# Check for model management support
try:
    from .models import ModelManager, MODELS, format_model_info
    from .setup import SetupWizard
    HAS_MODELS = True
except ImportError:
    HAS_MODELS = False

# Check for RAG support
try:
    from .rag import MicroRAG, quick_rag
    HAS_RAG = True
except ImportError:
    HAS_RAG = False


def cmd_generate(args):
    """Generate text from a prompt."""
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    
    # Get prompt from file or command line
    if args.file:
        with open(args.file, 'r') as f:
            prompt = f.read()
    else:
        prompt = args.prompt
    
    response = llm.generate(prompt)
    print(response)


def cmd_chat(args):
    """Interactive chat mode."""
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    history = []
    
    print("🤖 Chi_LLM Chat (type 'exit' or 'quit' to stop)")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\nAI: ", end="", flush=True)
            response = llm.chat(user_input, history=history)
            print(response)
            
            # Update history
            history.append({"user": user_input, "assistant": response})
            
            # Keep only last 10 exchanges
            if len(history) > 10:
                history = history[-10:]
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def cmd_complete(args):
    """Complete/continue text."""
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    
    # Get text from file or command line
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        text = args.text
    
    response = llm.complete(text)
    print(response)


def cmd_ask(args):
    """Ask a question."""
    llm = MicroLLM(temperature=args.temperature, max_tokens=args.max_tokens)
    
    # Get context from file if provided
    context = None
    if args.context_file:
        with open(args.context_file, 'r') as f:
            context = f.read()
    elif args.context:
        context = args.context
    
    response = llm.ask(args.question, context=context)
    print(response)


def cmd_analyze(args):
    """Analyze code (backward compatibility)."""
    # Override GPU detection if requested
    if args.no_gpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
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


def cmd_extract(args):
    """Extract structured data from text."""
    llm = MicroLLM()
    
    # Get text from file or command line
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        text = args.text
    
    # Parse schema if provided
    schema = None
    if args.schema:
        schema = json.loads(args.schema)
    
    response = llm.extract(text, format=args.format, schema=schema)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(response)
        print(f"✅ Extracted data saved to {args.output}")
    else:
        print(response)


def cmd_summarize(args):
    """Summarize text."""
    llm = MicroLLM()
    
    # Get text from file or command line
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        text = args.text
    
    response = llm.summarize(text, max_sentences=args.sentences)
    print(response)


def cmd_translate(args):
    """Translate text."""
    llm = MicroLLM()
    
    # Get text from file or command line
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        text = args.text
    
    response = llm.translate(text, target_language=args.language)
    print(response)


def cmd_classify(args):
    """Classify text into categories."""
    llm = MicroLLM()
    
    # Get text from file or command line
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        text = args.text
    
    # Parse categories
    categories = args.categories.split(',')
    
    response = llm.classify(text, categories=categories)
    print(f"Classification: {response}")


def cmd_template(args):
    """Generate text using prompt templates."""
    llm = MicroLLM()
    templates = PromptTemplates()
    
    # Map template names to methods
    template_map = {
        'code-review': lambda: templates.code_review(args.input, language=args.language),
        'explain-code': lambda: templates.explain_code(args.input),
        'fix-error': lambda: templates.fix_error(args.input, args.error),
        'write-tests': lambda: templates.write_tests(args.input, framework=args.framework),
        'optimize': lambda: templates.optimize_code(args.input),
        'document': lambda: templates.document_code(args.input, style=args.style),
        'sql': lambda: templates.sql_from_description(args.input),
        'regex': lambda: templates.regex_from_description(args.input),
        'email': lambda: templates.email_draft(args.input, tone=args.tone),
        'commit': lambda: templates.commit_message(args.input),
        'user-story': lambda: templates.user_story(args.input),
    }
    
    if args.template not in template_map:
        print(f"❌ Unknown template: {args.template}")
        print(f"Available templates: {', '.join(template_map.keys())}")
        sys.exit(1)
    
    # Get input from file if provided
    if args.file:
        with open(args.file, 'r') as f:
            args.input = f.read()
    
    prompt = template_map[args.template]()
    response = llm.generate(prompt)
    print(response)


def cmd_rag(args):
    """RAG commands."""
    if not HAS_RAG:
        print("❌ RAG features not installed. Install with: pip install chi-llm[rag]")
        sys.exit(1)
    
    if args.rag_command == 'query':
        # Quick query without persistence
        if args.documents:
            docs = []
            for doc_file in args.documents:
                with open(doc_file, 'r') as f:
                    docs.append(f.read())
            
            answer = quick_rag(args.question, docs)
            print(answer)
        
        # Query existing database
        elif args.db:
            rag = MicroRAG(db_path=args.db)
            result = rag.query(args.question, include_sources=args.sources)
            
            if args.sources:
                print(f"Answer: {result['answer']}")
                print(f"\nSources ({len(result['sources'])}):")
                for i, source in enumerate(result['sources'], 1):
                    print(f"  {i}. {source['content'][:100]}...")
            else:
                print(result)
            
            rag.close()
        
        # Load from config
        elif args.config:
            rag = MicroRAG.from_config(args.config)
            answer = rag.query(args.question)
            print(answer)
            rag.close()
        
        else:
            print("❌ Provide --documents, --db, or --config")
            sys.exit(1)
    
    elif args.rag_command == 'add':
        if not args.db:
            print("❌ Specify database with --db")
            sys.exit(1)
        
        rag = MicroRAG(db_path=args.db)
        
        # Add documents from files
        for doc_file in args.documents:
            with open(doc_file, 'r') as f:
                content = f.read()
                doc_id = rag.add_document(content)
                print(f"✅ Added document: {doc_file} (ID: {doc_id})")
        
        print(f"Total documents: {rag.count_documents()}")
        rag.close()
    
    elif args.rag_command == 'search':
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
    
    elif args.rag_command == 'info':
        if not args.db:
            print("❌ Specify database with --db")
            sys.exit(1)
        
        rag = MicroRAG(db_path=args.db)
        count = rag.count_documents()
        print(f"📚 Database: {args.db}")
        print(f"📄 Documents: {count}")
        rag.close()


def cmd_setup(args):
    """Run interactive setup wizard."""
    if not HAS_MODELS:
        print("❌ Model management not available")
        return
    
    wizard = SetupWizard()
    wizard.run()


def cmd_models(args):
    """Model management commands."""
    if not HAS_MODELS:
        print("❌ Model management not available")
        return
    
    manager = ModelManager()
    
    if args.models_command == 'list':
        # List all models
        print("📦 Available Models:\n")
        current = manager.get_current_model()
        
        for model in MODELS.values():
            is_downloaded = manager.is_downloaded(model.id)
            is_current = model.id == current.id
            
            status = ""
            if is_current:
                status = " [CURRENT]"
            elif is_downloaded:
                status = " [Downloaded]"
            
            print(f"• {model.name} ({model.size}){status}")
            print(f"  ID: {model.id} | Size: {model.file_size_mb}MB | RAM: {model.recommended_ram_gb}GB")
            print(f"  {model.description}\n")
    
    elif args.models_command == 'current':
        # Show current model
        current = manager.get_current_model()
        stats = manager.get_model_stats()
        print(format_model_info(current, True, True))
        print(f"\n📁 Config source: {stats['config_source']}")  
        print(f"   Path: {stats['config_path']}")
    
    elif args.models_command == 'set':
        # Set default model
        if args.model_id not in MODELS:
            print(f"❌ Unknown model: {args.model_id}")
            print("Available models:", ", ".join(MODELS.keys()))
            return
        
        if not manager.is_downloaded(args.model_id):
            print(f"⚠️  Model {args.model_id} is not downloaded.")
            print("Run 'chi-llm setup' to download it first.")
            return
        
        # Check for --local flag
        save_target = 'local' if hasattr(args, 'local') and args.local else 'global'
        manager.set_default_model(args.model_id, save_target=save_target)
        model = MODELS[args.model_id]
        location = "locally" if save_target == 'local' else "globally"
        print(f"✅ {model.name} is now the default model {location}!")
    
    elif args.models_command == 'info':
        # Show model info
        if args.model_id not in MODELS:
            print(f"❌ Unknown model: {args.model_id}")
            return
        
        model = MODELS[args.model_id]
        is_downloaded = manager.is_downloaded(args.model_id)
        is_current = args.model_id == manager.get_current_model().id
        print(format_model_info(model, is_downloaded, is_current))


def cmd_interactive(args):
    """Interactive mode with multiple features."""
    print("🤖 Chi_LLM Interactive Mode")
    print("Type 'help' for available commands, 'exit' to quit")
    print("-" * 60)
    
    llm = MicroLLM()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("""
Available commands:
  chat          - Start chat conversation
  generate TEXT - Generate text
  complete TEXT - Complete text
  ask QUESTION  - Ask a question
  summarize TEXT - Summarize text
  translate TEXT - Translate to English
  help          - Show this help
  exit          - Exit interactive mode
                """)
                continue
            
            # Parse command
            parts = user_input.split(' ', 1)
            command = parts[0].lower()
            text = parts[1] if len(parts) > 1 else ""
            
            if command == 'chat':
                print("Starting chat mode (type 'back' to return)...")
                chat_history = []
                while True:
                    chat_input = input("You: ").strip()
                    if chat_input.lower() == 'back':
                        break
                    response = llm.chat(chat_input, history=chat_history)
                    print(f"AI: {response}")
                    chat_history.append({"user": chat_input, "assistant": response})
            
            elif command == 'generate':
                response = llm.generate(text)
                print(response)
            
            elif command == 'complete':
                response = llm.complete(text)
                print(response)
            
            elif command == 'ask':
                response = llm.ask(text)
                print(response)
            
            elif command == 'summarize':
                response = llm.summarize(text, max_sentences=3)
                print(response)
            
            elif command == 'translate':
                response = llm.translate(text, target_language="English")
                print(response)
            
            else:
                # Default to generation
                response = llm.generate(user_input)
                print(response)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chi_LLM - Zero Configuration Micro-LLM Library",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global arguments
    parser.add_argument('--version', action='version', version='chi_llm 2.1.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate text from prompt')
    gen_parser.add_argument('prompt', nargs='?', help='Text prompt')
    gen_parser.add_argument('-f', '--file', help='Read prompt from file')
    gen_parser.add_argument('-t', '--temperature', type=float, default=0.7, help='Temperature (0.0-1.0)')
    gen_parser.add_argument('-m', '--max-tokens', type=int, default=4096, help='Max tokens')
    gen_parser.set_defaults(func=cmd_generate)
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat mode')
    chat_parser.add_argument('-t', '--temperature', type=float, default=0.7, help='Temperature')
    chat_parser.add_argument('-m', '--max-tokens', type=int, default=4096, help='Max tokens')
    chat_parser.set_defaults(func=cmd_chat)
    
    # Complete command
    comp_parser = subparsers.add_parser('complete', help='Complete/continue text')
    comp_parser.add_argument('text', nargs='?', help='Text to complete')
    comp_parser.add_argument('-f', '--file', help='Read text from file')
    comp_parser.add_argument('-t', '--temperature', type=float, default=0.7, help='Temperature')
    comp_parser.add_argument('-m', '--max-tokens', type=int, default=4096, help='Max tokens')
    comp_parser.set_defaults(func=cmd_complete)
    
    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Ask a question')
    ask_parser.add_argument('question', help='Question to ask')
    ask_parser.add_argument('-c', '--context', help='Context for the question')
    ask_parser.add_argument('-cf', '--context-file', help='Read context from file')
    ask_parser.add_argument('-t', '--temperature', type=float, default=0.7, help='Temperature')
    ask_parser.add_argument('-m', '--max-tokens', type=int, default=4096, help='Max tokens')
    ask_parser.set_defaults(func=cmd_ask)
    
    # Analyze command (backward compatibility)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code file')
    analyze_parser.add_argument('file_path', help='Path to code file')
    analyze_parser.add_argument('-q', '--question', default=DEFAULT_QUESTION, help='Question about code')
    analyze_parser.add_argument('--no-gpu', action='store_true', help='Force CPU mode')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract structured data')
    extract_parser.add_argument('text', nargs='?', help='Text to extract from')
    extract_parser.add_argument('-f', '--file', help='Read text from file')
    extract_parser.add_argument('--format', default='json', choices=['json', 'yaml'], help='Output format')
    extract_parser.add_argument('--schema', help='JSON schema for extraction')
    extract_parser.add_argument('-o', '--output', help='Save to file')
    extract_parser.set_defaults(func=cmd_extract)
    
    # Summarize command
    sum_parser = subparsers.add_parser('summarize', help='Summarize text')
    sum_parser.add_argument('text', nargs='?', help='Text to summarize')
    sum_parser.add_argument('-f', '--file', help='Read text from file')
    sum_parser.add_argument('-s', '--sentences', type=int, default=3, help='Max sentences')
    sum_parser.set_defaults(func=cmd_summarize)
    
    # Translate command
    trans_parser = subparsers.add_parser('translate', help='Translate text')
    trans_parser.add_argument('text', nargs='?', help='Text to translate')
    trans_parser.add_argument('-f', '--file', help='Read text from file')
    trans_parser.add_argument('-l', '--language', default='English', help='Target language')
    trans_parser.set_defaults(func=cmd_translate)
    
    # Classify command
    class_parser = subparsers.add_parser('classify', help='Classify text')
    class_parser.add_argument('text', nargs='?', help='Text to classify')
    class_parser.add_argument('-f', '--file', help='Read text from file')
    class_parser.add_argument('-c', '--categories', required=True, help='Comma-separated categories')
    class_parser.set_defaults(func=cmd_classify)
    
    # Template command
    tmpl_parser = subparsers.add_parser('template', help='Use prompt templates')
    tmpl_parser.add_argument('template', choices=[
        'code-review', 'explain-code', 'fix-error', 'write-tests',
        'optimize', 'document', 'sql', 'regex', 'email',
        'commit', 'user-story'
    ], help='Template to use')
    tmpl_parser.add_argument('input', nargs='?', help='Input text')
    tmpl_parser.add_argument('-f', '--file', help='Read input from file')
    tmpl_parser.add_argument('--language', help='Programming language')
    tmpl_parser.add_argument('--error', help='Error message (for fix-error)')
    tmpl_parser.add_argument('--framework', default='pytest', help='Test framework')
    tmpl_parser.add_argument('--style', default='google', help='Doc style')
    tmpl_parser.add_argument('--tone', default='professional', help='Email tone')
    tmpl_parser.set_defaults(func=cmd_template)
    
    # RAG command
    if HAS_RAG:
        rag_parser = subparsers.add_parser('rag', help='RAG operations')
        rag_sub = rag_parser.add_subparsers(dest='rag_command', help='RAG commands')
        
        # RAG query
        rag_query = rag_sub.add_parser('query', help='Query documents')
        rag_query.add_argument('question', help='Question to ask')
        rag_query.add_argument('-d', '--documents', nargs='+', help='Document files')
        rag_query.add_argument('--db', help='Database path')
        rag_query.add_argument('--config', help='Config file')
        rag_query.add_argument('-s', '--sources', action='store_true', help='Include sources')
        
        # RAG add
        rag_add = rag_sub.add_parser('add', help='Add documents to database')
        rag_add.add_argument('documents', nargs='+', help='Document files to add')
        rag_add.add_argument('--db', required=True, help='Database path')
        
        # RAG search
        rag_search = rag_sub.add_parser('search', help='Search documents')
        rag_search.add_argument('query', help='Search query')
        rag_search.add_argument('--db', required=True, help='Database path')
        rag_search.add_argument('-k', '--top-k', type=int, default=3, help='Number of results')
        
        # RAG info
        rag_info = rag_sub.add_parser('info', help='Database info')
        rag_info.add_argument('--db', required=True, help='Database path')
        
        rag_parser.set_defaults(func=cmd_rag)
    
    # Setup command
    if HAS_MODELS:
        setup_parser = subparsers.add_parser('setup', help='Interactive model setup wizard')
        setup_parser.set_defaults(func=cmd_setup)
        
        # Models command
        models_parser = subparsers.add_parser('models', help='Model management')
        models_sub = models_parser.add_subparsers(dest='models_command', help='Model commands')
        
        # Models list
        models_list = models_sub.add_parser('list', help='List all available models')
        
        # Models current
        models_current = models_sub.add_parser('current', help='Show current model')
        
        # Models set
        models_set = models_sub.add_parser('set', help='Set default model')
        models_set.add_argument('model_id', help='Model ID (e.g., phi3-mini, qwen2-1.5b)')
        models_set.add_argument('--local', action='store_true', help='Save to local project config')
        
        # Models info
        models_info = models_sub.add_parser('info', help='Show model details')
        models_info.add_argument('model_id', help='Model ID')
        
        models_parser.set_defaults(func=cmd_models)
    
    # Interactive mode
    inter_parser = subparsers.add_parser('interactive', help='Interactive mode')
    inter_parser.set_defaults(func=cmd_interactive)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()