#!/usr/bin/env python3
"""
Enterprise RAG Functionality Tests
"""

import requests
import json
import time

MCP_SERVER_URL = "http://localhost:8001"

def test_rag_stats():
    """Test RAG statistics endpoint"""
    print("\n📊 Testing RAG Stats...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/rag/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ RAG Stats retrieved")
            print(f"   📄 Documents: {data['documents']['total']}")
            print(f"   🔢 Vectors: {data['vectors'].get('points_count', 0)}")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_create_document():
    """Test document creation with RAG"""
    print("\n📝 Testing Document Creation...")
    try:
        doc_data = {
            "title": "Test Document: AI Platform Overview",
            "content": """
            This is a test document about our AI platform.

            Our platform supports multiple LLM models including:
            - Qwen 2.5 (local model)
            - Taiwan Government LLMs (10 models)
            - OpenAI GPT series
            - Claude series from Anthropic
            - Google Gemini

            Key features:
            1. Multi-model support
            2. Enterprise RAG capabilities
            3. Vector search powered by Qdrant
            4. Document management
            5. Semantic search

            The platform uses sentence transformers for embedding generation
            and provides comprehensive document processing capabilities.
            """,
            "category": "Documentation",
            "tags": ["AI", "Platform", "Overview"],
            "metadata": {"author": "test", "version": "1.0"}
        }

        response = requests.post(
            f"{MCP_SERVER_URL}/rag/documents/text",
            json=doc_data
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Document created: ID {data['doc_id']}")
            print(f"   📊 Chunks created: {data['chunks_count']}")
            print(f"   📏 Content length: {data['content_length']}")
            return data['doc_id']
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def test_semantic_search(query: str):
    """Test semantic search"""
    print(f"\n🔍 Testing Semantic Search: '{query}'...")
    try:
        search_data = {
            "query": query,
            "top_k": 3,
            "similarity_threshold": 0.3
        }

        response = requests.post(
            f"{MCP_SERVER_URL}/rag/search",
            json=search_data
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Search completed: {data['count']} results")

            for i, result in enumerate(data['results'], 1):
                print(f"\n   Result {i}:")
                print(f"   📄 Title: {result['title']}")
                print(f"   📊 Score: {result['score']:.3f}")
                print(f"   📝 Content: {result['content'][:100]}...")

            return len(data['results']) > 0
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_list_documents():
    """Test document listing"""
    print("\n📋 Testing Document Listing...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/rag/documents?limit=10")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Documents retrieved: {len(data['documents'])} / {data['total']}")

            for doc in data['documents'][:3]:
                print(f"   📄 ID {doc['id']}: {doc['title']}")

            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_get_document(doc_id: int):
    """Test getting document details"""
    print(f"\n📖 Testing Get Document: ID {doc_id}...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/rag/documents/{doc_id}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Document retrieved")
            print(f"   📄 Title: {data['title']}")
            print(f"   📂 Category: {data.get('category', 'N/A')}")
            print(f"   🏷️  Tags: {', '.join(data.get('tags', []))}")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def main():
    """Run all RAG tests"""
    print("="* 80)
    print(" Enterprise RAG System Tests")
    print("="  * 80)

    results = []

    # Test 1: RAG Stats
    results.append(("RAG Stats", test_rag_stats()))
    time.sleep(1)

    # Test 2: Create Document
    doc_id = test_create_document()
    results.append(("Create Document", doc_id is not None))

    if doc_id:
        # Wait for indexing
        print("\n⏳ Waiting for document indexing...")
        time.sleep(3)

        # Test 3: Get Document
        results.append(("Get Document", test_get_document(doc_id)))
        time.sleep(1)

        # Test 4: List Documents
        results.append(("List Documents", test_list_documents()))
        time.sleep(1)

        # Test 5: Semantic Search - Multiple queries
        queries = [
            "What models does the platform support?",
            "Tell me about vector search",
            "Document processing features"
        ]

        for query in queries:
            results.append((f"Search: {query[:30]}", test_semantic_search(query)))
            time.sleep(1)

    # Summary
    print("\n" + "=" * 80)
    print(" Test Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
