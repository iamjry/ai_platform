"""
SQL Database Tools for Agent
Provides safe SQL query execution and database inspection capabilities
"""

from typing import Dict, List, Optional, Any
import asyncpg
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# SQL Tool Definitions for Agent
SQL_TOOLS = [
    {
        "name": "sql_query",
        "description": "Execute a READ-ONLY SQL query on the database. Only SELECT statements are allowed. Returns query results as a list of dictionaries. Use this to query data from tables.",
        "category": "database",
        "parameters": {
            "query": "string - SQL SELECT query to execute",
            "limit": "integer (optional, default 100) - Maximum number of rows to return",
            "timeout": "integer (optional, default 30) - Query timeout in seconds"
        },
        "examples": [
            "SELECT * FROM users WHERE created_at > '2024-01-01' LIMIT 10",
            "SELECT COUNT(*) as total FROM orders WHERE status = 'completed'",
            "SELECT category, COUNT(*) as count FROM products GROUP BY category"
        ]
    },
    {
        "name": "sql_get_schema",
        "description": "Get database schema information including tables, columns, and their types. Use this before writing queries to understand the database structure.",
        "category": "database",
        "parameters": {
            "table_name": "string (optional) - Specific table name to get schema for. If not provided, returns all tables.",
            "include_indexes": "boolean (optional, default false) - Include index information"
        }
    },
    {
        "name": "sql_list_tables",
        "description": "List all tables in the database with row counts and descriptions.",
        "category": "database",
        "parameters": {}
    },
    {
        "name": "sql_explain_query",
        "description": "Explain how a SQL query will be executed (query plan). Useful for understanding performance.",
        "category": "database",
        "parameters": {
            "query": "string - SQL query to explain"
        }
    }
]


class SQLQueryValidator:
    """Validates SQL queries for safety"""

    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE',
        'ALTER', 'CREATE', 'REPLACE', 'GRANT', 'REVOKE',
        'EXEC', 'EXECUTE', 'SCRIPT', 'SCRIPT'
    ]

    # Allowed SELECT-related keywords
    ALLOWED_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT',
        'ON', 'AND', 'OR', 'GROUP', 'BY', 'HAVING', 'ORDER', 'LIMIT',
        'OFFSET', 'AS', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
        'UNION', 'WITH', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'IN',
        'EXISTS', 'NOT', 'NULL', 'IS', 'LIKE', 'BETWEEN', 'ASC', 'DESC'
    ]

    @staticmethod
    def is_safe_query(query: str) -> tuple[bool, str]:
        """
        Check if a SQL query is safe to execute

        Returns:
            (is_safe: bool, message: str)
        """
        query_upper = query.upper().strip()

        # Must start with SELECT or WITH (for CTEs)
        if not (query_upper.startswith('SELECT') or query_upper.startswith('WITH')):
            return False, "Only SELECT queries (or WITH...SELECT) are allowed"

        # Check for dangerous keywords
        for keyword in SQLQueryValidator.DANGEROUS_KEYWORDS:
            # Use word boundary to avoid false positives (e.g., "UPDATE" in column name)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"

        # Check for semicolons (multiple statements)
        if ';' in query.rstrip(';'):
            return False, "Multiple statements are not allowed (semicolons detected)"

        return True, "Query is safe"


async def sql_query_tool(
    db_pool: asyncpg.pool.Pool,
    query: str,
    limit: int = 100,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Execute a READ-ONLY SQL query

    Args:
        db_pool: Database connection pool
        query: SQL query to execute
        limit: Maximum number of rows to return
        timeout: Query timeout in seconds

    Returns:
        Dict with query results, metadata, and execution info
    """
    try:
        # Validate query safety
        is_safe, message = SQLQueryValidator.is_safe_query(query)
        if not is_safe:
            return {
                "success": False,
                "error": f"Query validation failed: {message}",
                "query": query
            }

        # Add LIMIT if not present
        query_upper = query.upper()
        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        # Execute query
        start_time = datetime.now()

        async with db_pool.acquire() as conn:
            # Set statement timeout
            await conn.execute(f"SET statement_timeout = {timeout * 1000}")

            # Execute query
            rows = await conn.fetch(query)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Convert to list of dicts
        results = [dict(row) for row in rows]

        # Get column names and types
        column_info = []
        if results:
            first_row = results[0]
            column_info = [
                {"name": col, "type": type(val).__name__}
                for col, val in first_row.items()
            ]

        return {
            "success": True,
            "query": query,
            "rows_returned": len(results),
            "results": results,
            "columns": column_info,
            "execution_time_seconds": round(execution_time, 3),
            "executed_at": end_time.isoformat()
        }

    except asyncpg.exceptions.QueryCanceledError:
        return {
            "success": False,
            "error": f"Query timeout after {timeout} seconds",
            "query": query
        }
    except asyncpg.exceptions.PostgresError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "error_code": e.sqlstate if hasattr(e, 'sqlstate') else None,
            "query": query
        }
    except Exception as e:
        logger.error(f"SQL query error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "query": query
        }


async def sql_get_schema_tool(
    db_pool: asyncpg.pool.Pool,
    table_name: Optional[str] = None,
    include_indexes: bool = False
) -> Dict[str, Any]:
    """
    Get database schema information

    Args:
        db_pool: Database connection pool
        table_name: Specific table to get schema for (optional)
        include_indexes: Include index information

    Returns:
        Dict with schema information
    """
    try:
        async with db_pool.acquire() as conn:
            if table_name:
                # Get schema for specific table
                query = """
                SELECT
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale,
                    tc.constraint_type
                FROM information_schema.columns c
                LEFT JOIN information_schema.constraint_column_usage ccu
                    ON c.table_name = ccu.table_name
                    AND c.column_name = ccu.column_name
                LEFT JOIN information_schema.table_constraints tc
                    ON ccu.constraint_name = tc.constraint_name
                WHERE c.table_schema = 'public'
                    AND c.table_name = $1
                ORDER BY c.ordinal_position
                """
                rows = await conn.fetch(query, table_name)

                if not rows:
                    return {
                        "success": False,
                        "error": f"Table '{table_name}' not found"
                    }

                columns = []
                for row in rows:
                    col_info = {
                        "name": row['column_name'],
                        "type": row['data_type'],
                        "nullable": row['is_nullable'] == 'YES',
                        "default": row['column_default']
                    }

                    if row['character_maximum_length']:
                        col_info['max_length'] = row['character_maximum_length']
                    if row['numeric_precision']:
                        col_info['precision'] = row['numeric_precision']
                    if row['constraint_type']:
                        col_info['constraint'] = row['constraint_type']

                    columns.append(col_info)

                result = {
                    "success": True,
                    "table_name": table_name,
                    "columns": columns
                }

                # Get indexes if requested
                if include_indexes:
                    idx_query = """
                    SELECT
                        i.relname as index_name,
                        a.attname as column_name,
                        am.amname as index_type
                    FROM pg_class t
                    JOIN pg_index ix ON t.oid = ix.indrelid
                    JOIN pg_class i ON i.oid = ix.indexrelid
                    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                    JOIN pg_am am ON i.relam = am.oid
                    WHERE t.relname = $1
                    ORDER BY i.relname, a.attnum
                    """
                    idx_rows = await conn.fetch(idx_query, table_name)

                    indexes = {}
                    for row in idx_rows:
                        idx_name = row['index_name']
                        if idx_name not in indexes:
                            indexes[idx_name] = {
                                "type": row['index_type'],
                                "columns": []
                            }
                        indexes[idx_name]['columns'].append(row['column_name'])

                    result['indexes'] = indexes

                return result

            else:
                # Get all tables
                query = """
                SELECT
                    t.table_name,
                    obj_description((quote_ident(t.table_schema)||'.'||quote_ident(t.table_name))::regclass) as description,
                    (SELECT COUNT(*) FROM information_schema.columns c
                     WHERE c.table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE t.table_schema = 'public'
                    AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
                """
                rows = await conn.fetch(query)

                tables = []
                for row in rows:
                    tables.append({
                        "name": row['table_name'],
                        "description": row['description'],
                        "column_count": row['column_count']
                    })

                return {
                    "success": True,
                    "tables": tables,
                    "table_count": len(tables)
                }

    except Exception as e:
        logger.error(f"Get schema error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def sql_list_tables_tool(db_pool: asyncpg.pool.Pool) -> Dict[str, Any]:
    """
    List all tables with row counts

    Args:
        db_pool: Database connection pool

    Returns:
        Dict with table list and metadata
    """
    try:
        async with db_pool.acquire() as conn:
            query = """
            SELECT
                t.table_name,
                obj_description((quote_ident(t.table_schema)||'.'||quote_ident(t.table_name))::regclass) as description,
                (SELECT COUNT(*) FROM information_schema.columns c
                 WHERE c.table_name = t.table_name) as column_count,
                pg_size_pretty(pg_total_relation_size(quote_ident(t.table_schema)||'.'||quote_ident(t.table_name))) as size
            FROM information_schema.tables t
            WHERE t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
            """
            rows = await conn.fetch(query)

            tables = []
            for row in rows:
                table_info = {
                    "name": row['table_name'],
                    "description": row['description'] or "No description",
                    "columns": row['column_count'],
                    "size": row['size']
                }

                # Get approximate row count
                try:
                    count_query = f"SELECT COUNT(*) as cnt FROM {row['table_name']}"
                    count_row = await conn.fetchrow(count_query)
                    table_info['rows'] = count_row['cnt']
                except:
                    table_info['rows'] = "N/A"

                tables.append(table_info)

            return {
                "success": True,
                "tables": tables,
                "total_tables": len(tables)
            }

    except Exception as e:
        logger.error(f"List tables error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def sql_explain_query_tool(
    db_pool: asyncpg.pool.Pool,
    query: str
) -> Dict[str, Any]:
    """
    Explain a SQL query execution plan

    Args:
        db_pool: Database connection pool
        query: SQL query to explain

    Returns:
        Dict with query execution plan
    """
    try:
        # Validate query safety
        is_safe, message = SQLQueryValidator.is_safe_query(query)
        if not is_safe:
            return {
                "success": False,
                "error": f"Query validation failed: {message}"
            }

        async with db_pool.acquire() as conn:
            # Get query plan
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE false) {query}"
            rows = await conn.fetch(explain_query)

            plan = rows[0]['QUERY PLAN'] if rows else []

            return {
                "success": True,
                "query": query,
                "execution_plan": plan
            }

    except Exception as e:
        logger.error(f"Explain query error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
