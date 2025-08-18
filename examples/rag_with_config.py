#!/usr/bin/env python3
"""
Example of using MicroRAG with YAML configuration.
"""

from chi_llm.rag import MicroRAG


def main():
    print("🤖 MicroRAG with YAML Configuration\n")
    
    # Load RAG system from config file
    print("Loading RAG from config file...")
    rag = MicroRAG.from_config("rag_config.yaml")
    
    print(f"Documents loaded: {rag.count_documents()}")
    print("-" * 40)
    
    # Query the pre-loaded knowledge base
    questions = [
        "What is chi_llm?",
        "What model does it use?",
        "How do I install RAG features?",
        "Does it require API keys?",
    ]
    
    for question in questions:
        print(f"\n❓ {question}")
        
        # Get answer with sources
        result = rag.query(question, include_sources=True)
        
        print(f"💡 {result['answer']}")
        
        if result['sources']:
            print(f"📚 Based on {len(result['sources'])} sources")
            for i, source in enumerate(result['sources'], 1):
                print(f"   {i}. {source['content'][:100]}...")
    
    # Add more documents dynamically
    print("\n" + "=" * 40)
    print("Adding new knowledge dynamically...")
    
    new_facts = [
        "MicroRAG uses sentence-transformers for embeddings.",
        "SQLite-vec enables vector search in SQLite databases.",
        "The system works completely offline after initial model download.",
    ]
    
    for fact in new_facts:
        rag.add_document(fact, metadata={"source": "runtime", "type": "fact"})
    
    print(f"Updated document count: {rag.count_documents()}")
    
    # Query with the new knowledge
    print("\n❓ How does MicroRAG create embeddings?")
    answer = rag.query("How does MicroRAG create embeddings?")
    print(f"💡 {answer}")
    
    # Search for specific documents
    print("\n" + "=" * 40)
    print("Searching for specific topics...")
    
    search_terms = ["embeddings", "offline", "SQLite"]
    
    for term in search_terms:
        print(f"\n🔍 Searching for: {term}")
        results = rag.search(term, top_k=2)
        
        if results:
            for i, doc in enumerate(results, 1):
                print(f"   {i}. {doc.content[:100]}...")
                if doc.metadata:
                    print(f"      Type: {doc.metadata.get('type', 'unknown')}")
        else:
            print("   No results found")
    
    # Clean up
    rag.close()
    print("\n✅ Configuration example completed!")


if __name__ == "__main__":
    main()