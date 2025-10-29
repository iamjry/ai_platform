"""
AI Platform - Locust Load Testing
==================================

This script provides comprehensive load testing for the AI Platform using Locust.

Usage:
    # Install locust
    pip install locust

    # Run with Web UI
    locust -f locustfile.py --host=http://localhost:8001

    # Run headless
    locust -f locustfile.py --host=http://localhost:8001 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

    # View results at http://localhost:8089
"""

from locust import HttpUser, task, between, events
import json
import random
import time
from datetime import datetime


class AIToolUser(HttpUser):
    """Simulates a user using various AI Platform tools"""

    # Wait 1-5 seconds between tasks
    wait_time = between(1, 5)

    def on_start(self):
        """Called when a simulated user starts"""
        self.test_queries = [
            "What is artificial intelligence?",
            "Explain machine learning",
            "How do neural networks work?",
            "What is deep learning?",
            "Tell me about natural language processing"
        ]
        self.document_ids = list(range(1, 11))  # Assume 10 test documents

    @task(5)
    def health_check(self):
        """Test health check endpoint (high weight - frequent)"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(10)
    def search_knowledge_base(self):
        """Test knowledge base search (very common operation)"""
        query = random.choice(self.test_queries)

        with self.client.post(
            "/tools/search_knowledge_base",
            json={
                "query": query,
                "limit": 5
            },
            catch_response=True,
            name="Search Knowledge Base"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "result" in data:
                        response.success()
                    else:
                        response.failure("No result in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status {response.status_code}")

    @task(8)
    def semantic_search(self):
        """Test semantic search (common operation)"""
        query = random.choice(self.test_queries)

        with self.client.post(
            "/tools/semantic_search",
            json={
                "query": query,
                "top_k": 5,
                "similarity_threshold": 0.7
            },
            catch_response=True,
            name="Semantic Search"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)
    def web_search(self):
        """Test web search (less frequent, more expensive)"""
        query = random.choice([
            "latest AI developments",
            "machine learning news",
            "AI research papers"
        ])

        with self.client.post(
            "/tools/web_search",
            json={
                "query": query,
                "num_results": 3
            },
            catch_response=True,
            name="Web Search"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(6)
    def get_document(self):
        """Test document retrieval (common operation)"""
        doc_id = random.choice(self.document_ids)

        with self.client.post(
            "/tools/get_document",
            json={
                "document_id": doc_id
            },
            catch_response=True,
            name="Get Document"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(4)
    def query_database(self):
        """Test database queries"""
        query_types = ["get_users", "get_documents", "get_tasks"]
        query_type = random.choice(query_types)

        with self.client.post(
            "/tools/query_database",
            json={
                "query_type": query_type,
                "parameters": {}
            },
            catch_response=True,
            name=f"Query Database ({query_type})"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def analyze_data(self):
        """Test data analysis (less frequent)"""
        with self.client.post(
            "/tools/analyze_data",
            json={
                "data_source": "sales_data",
                "analysis_type": "descriptive",
                "options": {}
            },
            catch_response=True,
            name="Analyze Data"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def create_task(self):
        """Test task creation (infrequent)"""
        with self.client.post(
            "/tools/create_task",
            json={
                "title": f"Test Task {random.randint(1, 1000)}",
                "description": "Auto-generated test task",
                "assignee": "test_user"
            },
            catch_response=True,
            name="Create Task"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class LLMUser(HttpUser):
    """Simulates a user interacting with LLM endpoints"""

    wait_time = between(2, 8)  # LLM calls take longer

    def on_start(self):
        """Called when a simulated user starts"""
        self.prompts = [
            "Write a short poem about AI",
            "Explain quantum computing in simple terms",
            "What are the benefits of cloud computing?",
            "Describe the future of technology",
            "How does blockchain work?"
        ]

    @task
    def chat_completion(self):
        """Test LLM chat completion (simplified)"""
        prompt = random.choice(self.prompts)

        # Note: This is a simplified example
        # Actual implementation depends on your agent service API
        with self.client.post(
            "/agent/chat",
            json={
                "message": prompt,
                "model": "qwen2.5",
                "temperature": 0.7,
                "max_tokens": 200
            },
            catch_response=True,
            name="LLM Chat Completion",
            timeout=30  # LLM calls take longer
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "response" in data or "message" in data:
                        response.success()
                    else:
                        response.failure("No response in data")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status {response.status_code}")


class MixedWorkloadUser(HttpUser):
    """Simulates realistic mixed workload"""

    wait_time = between(1, 10)

    tasks = {
        AIToolUser.search_knowledge_base: 30,
        AIToolUser.semantic_search: 20,
        AIToolUser.get_document: 15,
        AIToolUser.query_database: 10,
        AIToolUser.web_search: 10,
        AIToolUser.health_check: 10,
        AIToolUser.analyze_data: 3,
        AIToolUser.create_task: 2
    }


# Event hooks for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print(f"\n{'='*60}")
    print(f"Starting load test at {datetime.now()}")
    print(f"Target: {environment.host}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print(f"\n{'='*60}")
    print(f"Test completed at {datetime.now()}")
    print(f"Total requests: {environment.stats.num_requests}")
    print(f"Total failures: {environment.stats.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"{'='*60}\n")


# Custom shape for ramping load
from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    A step load shape that gradually increases load

    Stages:
    1. 10 users for 2 minutes
    2. 50 users for 3 minutes
    3. 100 users for 3 minutes
    4. 200 users for 2 minutes
    """

    stages = [
        {"duration": 120, "users": 10, "spawn_rate": 5},
        {"duration": 300, "users": 50, "spawn_rate": 10},
        {"duration": 480, "users": 100, "spawn_rate": 10},
        {"duration": 600, "users": 200, "spawn_rate": 20},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None
