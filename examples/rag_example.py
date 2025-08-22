#!/usr/bin/env python3
"""
Example of using MicroRAG for document Q&A.
Install with: pip install chi-llm[rag]
"""

from chi_llm.rag import MicroRAG, quick_rag


def main():
    print("🤖 MicroRAG Example - Document Q&A\n")

    # Example 1: Quick RAG without persistence
    print("1️⃣ Quick RAG (no persistence):")
    print("-" * 40)

    documents = [
        "Python was created by Guido van Rossum in 1991.",
        "Python is a high-level, interpreted programming language.",
        "Python emphasizes code readability and uses indentation.",
        "The Zen of Python is a collection of aphorisms for Python design.",
        "Python 3.0 was released on December 3, 2008.",
    ]

    question = "Who created Python and when?"
    answer = quick_rag(question, documents)

    print(f"Question: {question}")
    print(f"Answer: {answer}\n")

    # Example 2: Persistent RAG with database
    print("2️⃣ Persistent RAG with database:")
    print("-" * 40)

    # Initialize RAG system
    rag = MicroRAG(db_path="./knowledge.db")

    # Add documents about AI/ML
    ml_docs = [
        "Machine Learning is a subset of artificial intelligence.",
        "Deep Learning uses neural networks with multiple layers.",
        "Supervised learning requires labeled training data.",
        "Unsupervised learning finds patterns without labels.",
        "Reinforcement learning learns through trial and error.",
        "Transfer learning reuses pre-trained models for new tasks.",
        "GPT models are based on the transformer architecture.",
        "BERT is bidirectional while GPT is autoregressive.",
    ]

    print(f"Adding {len(ml_docs)} documents to knowledge base...")
    rag.add_documents(ml_docs)
    print(f"Total documents: {rag.count_documents()}\n")

    # Query the knowledge base
    questions = [
        "What is the difference between supervised and unsupervised learning?",
        "How does transfer learning work?",
        "What architecture are GPT models based on?",
    ]

    for q in questions:
        print(f"Q: {q}")
        result = rag.query(q, include_sources=True)
        print(f"A: {result['answer']}")
        print(f"Sources: {len(result['sources'])} documents used\n")

    # Example 3: Adding documents with metadata
    print("3️⃣ Documents with metadata:")
    print("-" * 40)

    # Add documents with metadata
    rag.add_document(
        "NumPy is essential for numerical computing in Python.",
        metadata={"category": "library", "topic": "numerical"},
    )

    rag.add_document(
        "Pandas provides data structures for data analysis.",
        metadata={"category": "library", "topic": "data"},
    )

    rag.add_document(
        "Scikit-learn offers machine learning algorithms.",
        metadata={"category": "library", "topic": "ml"},
    )

    # Search with different queries
    search_queries = [
        "numerical computing",
        "data analysis tools",
        "machine learning libraries",
    ]

    for query in search_queries:
        print(f"Searching for: {query}")
        results = rag.search(query, top_k=2)
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.content[:50]}...")
            if doc.metadata:
                print(f"     Metadata: {doc.metadata}")
        print()

    # Clean up
    rag.close()
    print("✅ RAG example completed!")


if __name__ == "__main__":
    main()
