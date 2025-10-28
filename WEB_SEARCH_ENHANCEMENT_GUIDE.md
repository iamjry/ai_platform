# Web Search Enhancement Guide

## Overview

The AI Platform's web search functionality has been significantly enhanced with **RAG (Retrieval-Augmented Generation)** integration and multiple search provider support.

## Key Features

### 1. Multi-Provider Search

The system now supports **4 search providers**:

| Provider | Type | Cost | API Key Required | Best For |
|----------|------|------|------------------|----------|
| **DuckDuckGo** | Free | Free | No | Quick searches, privacy-focused |
| **Google Custom Search** | Official API | 100 free/day | Yes | High-quality results, structured data |
| **Tavily Search** | AI-optimized | Paid (free tier) | Yes | AI applications, summarized answers |
| **SerpAPI** | Aggregator | Paid | Yes | Production use, reliable Google results |

### 2. RAG Integration

- **Temporary Vectorization**: Search results are vectorized on-the-fly using sentence-transformers
- **Mixed Retrieval**: Combines web search results with existing documents from knowledge base
- **Semantic Ranking**: Results sorted by relevance scores

### 3. Intelligent Answer Generation

```
User Query → Multi-Provider Search → Vectorization → Semantic Search → Mix with Documents → Ranked Results
```

## Configuration

### Step 1: Add API Keys to `.env`

```bash
# Web Search API Keys
GOOGLE_SEARCH_API_KEY=your-google-api-key
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id
TAVILY_API_KEY=your-tavily-api-key
SERPAPI_API_KEY=your-serpapi-api-key
```

### Step 2: Obtain API Keys

#### DuckDuckGo (No Setup Required)
- Already enabled by default
- No API key needed
- Free unlimited searches

#### Google Custom Search API
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Custom Search API"
3. Create credentials (API key)
4. Create a [Custom Search Engine](https://programmablesearchengine.google.com/)
5. Note your Search Engine ID

#### Tavily Search API
1. Visit [Tavily.com](https://tavily.com/)
2. Sign up for an account
3. Get your API key from dashboard
4. Free tier: 1,000 requests/month

#### SerpAPI
1. Visit [SerpAPI.com](https://serpapi.com/)
2. Sign up for an account
3. Get your API key from dashboard
4. Free tier: 100 searches/month

## Usage Examples

### Example 1: Basic Web Search

```python
import httpx

response = await httpx.post("http://localhost:8001/tools/web_search", json={
    "query": "latest AI trends 2025",
    "num_results": 5
})

results = response.json()
```

### Example 2: Search with Specific Provider

```python
response = await httpx.post("http://localhost:8001/tools/web_search", json={
    "query": "Python async programming",
    "num_results": 10,
    "providers": ["tavily", "serpapi"]  # Only use these providers
})
```

### Example 3: RAG-Enhanced Search

```python
response = await httpx.post("http://localhost:8001/tools/web_search", json={
    "query": "Docker container orchestration",
    "num_results": 5,
    "use_rag": True,  # Enable vectorization
    "mix_with_documents": True  # Mix with knowledge base
})

# Results will include:
# - Web search results (vectorized)
# - Similar documents from knowledge base
# - All sorted by semantic relevance
```

### Example 4: Web-Only Search (No RAG)

```python
response = await httpx.post("http://localhost:8001/tools/web_search", json={
    "query": "current weather in Tokyo",
    "num_results": 3,
    "use_rag": False,  # Disable RAG for real-time queries
    "mix_with_documents": False
})
```

## Response Format

```json
{
  "query": "latest AI trends 2025",
  "results": [
    {
      "title": "AI Trends for 2025",
      "url": "https://example.com/ai-trends",
      "snippet": "The latest developments in AI...",
      "source": "Google (SerpAPI)",
      "rank": 1,
      "score": 0.92,
      "type": "web"
    },
    {
      "title": "AI Research Paper",
      "url": "",
      "snippet": "Internal document about AI...",
      "source": "Knowledge Base",
      "doc_id": 42,
      "score": 0.88,
      "type": "document"
    }
  ],
  "total_results": 12,
  "web_results_count": 8,
  "document_results_count": 4,
  "providers_used": ["duckduckgo", "tavily", "serpapi"],
  "rag_enabled": true,
  "mixed_with_documents": true,
  "search_time": "2.34s",
  "timestamp": "2025-10-28T15:45:00Z"
}
```

## Performance Optimization

### Parallel Search
- All providers are queried simultaneously
- Results are merged and deduplicated
- Typical search time: 1-3 seconds

### Caching Strategy
- Vectorization models cached in memory
- Qdrant handles vector similarity search efficiently
- No permanent storage of web search results

### Cost Management

| Provider | Free Tier | Cost After |
|----------|-----------|------------|
| DuckDuckGo | Unlimited | Always free |
| Google CSE | 100/day | $5 per 1,000 |
| Tavily | 1,000/month | $0.02 per search |
| SerpAPI | 100/month | $50 per 5,000 |

**Recommendation**:
- Use DuckDuckGo for development
- Add Tavily for AI-optimized results
- Use SerpAPI/Google for production

## Advanced Configuration

### Customize Search Providers

Edit `/services/mcp-server/search_service.py`:

```python
def _initialize_providers(self):
    # Add only desired providers
    self.providers = ["duckduckgo", "tavily"]  # Customize here
```

### Adjust RAG Parameters

Edit `/services/mcp-server/main.py` web_search endpoint:

```python
doc_results = await rag_service.semantic_search(
    query=request.query,
    limit=request.num_results,
    score_threshold=0.6  # Adjust relevance threshold (0.0-1.0)
)
```

### Change Vectorization Model

Edit `/services/mcp-server/rag_service.py`:

```python
def __init__(self):
    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Change model
    self.vector_size = 384  # Update dimension accordingly
```

Available models:
- `all-MiniLM-L6-v2` (384 dims) - Fast, good quality
- `all-mpnet-base-v2` (768 dims) - Better quality, slower
- `paraphrase-multilingual-MiniLM-L12-v2` (384 dims) - Multilingual

## Troubleshooting

### Issue: "No search providers available"

**Solution**:
- Check that at least one provider is configured
- DuckDuckGo should always be available (no API key needed)
- Check logs: `docker-compose logs mcp-server | grep "search provider"`

### Issue: Provider returns empty results

**Solution**:
- Check API key validity
- Verify rate limits not exceeded
- Check provider-specific logs for errors

### Issue: Slow search performance

**Solutions**:
- Reduce `num_results` parameter
- Disable `use_rag` for simple queries
- Use fewer providers: `providers=["duckduckgo"]`
- Check network connectivity to provider APIs

### Issue: RAG not working

**Solution**:
- Ensure Qdrant is running: `docker-compose ps qdrant`
- Check embedding model is loaded: Check logs for "Loading embedding model"
- Verify documents exist in knowledge base: `curl http://localhost:8001/rag/stats`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                   MCP Server (main.py)                           │
│              /tools/web_search endpoint                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        v                    v                    v
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ SearchService  │  │  RAGService    │  │    Qdrant      │
│ (4 providers)  │  │  (vectorize)   │  │  (similarity)  │
└────────┬───────┘  └────────┬───────┘  └────────┬───────┘
         │                   │                    │
         │ Web Results       │ Embeddings         │ Documents
         │                   │                    │
         └───────────────────┴────────────────────┘
                             │
                             v
                   ┌─────────────────────┐
                   │  Mixed & Ranked     │
                   │     Results         │
                   └─────────────────────┘
```

## Testing

### Test Search Providers

```bash
# Test DuckDuckGo
curl -X POST http://localhost:8001/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "providers": ["duckduckgo"]}'

# Test all providers
curl -X POST http://localhost:8001/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI trends 2025", "num_results": 3}'
```

### Test RAG Integration

```bash
# With RAG enabled
curl -X POST http://localhost:8001/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Docker deployment",
    "use_rag": true,
    "mix_with_documents": true
  }'
```

### Check Available Providers

```python
from search_service import search_service
print(search_service.get_available_providers())
# Output: ['duckduckgo', 'tavily', 'serpapi']
```

## Migration from Old Web Search

The old web search returned mock data. The new version:

**Before**:
```python
# Old: Mock results
results = [
    {"title": f"搜索結果 {i}",  "url": "https://example.com"}
]
```

**After**:
```python
# New: Real results with RAG
results = await search_service.search(query)
results = await rag_service.semantic_search(query)
# Mix and rank by relevance
```

**API Compatibility**:
- Same endpoint: `/tools/web_search`
- Additional optional parameters: `use_rag`, `mix_with_documents`, `providers`
- Response format enhanced but backward compatible

## Best Practices

1. **Development**: Use DuckDuckGo only (free, unlimited)
2. **Production**: Combine DuckDuckGo + Tavily + SerpAPI for redundancy
3. **AI Applications**: Tavily provides AI-optimized summaries
4. **Cost Optimization**: Monitor usage, set rate limits
5. **RAG Usage**:
   - Enable for research/knowledge queries
   - Disable for real-time data (weather, news)
6. **Error Handling**: Always check `total_results > 0` before using results

## Future Enhancements

- [ ] Add Bing Search API support
- [ ] Implement result caching (Redis)
- [ ] Add web scraping for full content
- [ ] Support image/video search
- [ ] Add search result persistence option
- [ ] Implement search analytics dashboard

## Support

For issues or questions:
- Check logs: `docker-compose logs mcp-server`
- Review configuration: `.env` file
- Test providers individually
- Check API key validity and quotas

---

**Version**: 2.3.0
**Last Updated**: 2025-10-28
**Author**: AI Platform Team
