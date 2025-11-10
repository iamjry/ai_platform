# SQL Database Tools for AI Agents

## Overview
This guide documents the SQL database tools available for AI Agents to query and inspect the database safely.

**Last Updated**: 2025-11-10
**Version**: 1.0

## Available SQL Tools

### 1. `sql_query` - Execute SQL Queries
Execute READ-ONLY SQL queries on the database. Only SELECT statements are allowed.

**Endpoint**: `POST /tools/sql_query`

**Parameters**:
- `query` (string, required): SQL SELECT query to execute
- `limit` (integer, optional, default: 100): Maximum number of rows to return
- `timeout` (integer, optional, default: 30): Query timeout in seconds

**Example Request**:
```json
{
  "query": "SELECT username, email, role FROM users WHERE is_active = true",
  "limit": 10,
  "timeout": 30
}
```

**Example Response**:
```json
{
  "success": true,
  "query": "SELECT username, email, role FROM users WHERE is_active = true LIMIT 10",
  "rows_returned": 3,
  "results": [
    {
      "username": "superadmin",
      "email": "superadmin@ai-platform.com",
      "role": "admin"
    },
    ...
  ],
  "columns": [
    {"name": "username", "type": "str"},
    {"name": "email", "type": "str"},
    {"name": "role", "type": "str"}
  ],
  "execution_time_seconds": 0.001,
  "executed_at": "2025-11-10T02:26:50.882877"
}
```

**Query Examples**:
```sql
-- Get active users
SELECT username, email, created_at FROM users WHERE is_active = true LIMIT 10

-- Count documents by category
SELECT category, COUNT(*) as count FROM documents GROUP BY category

-- Get recent audit logs
SELECT action, resource, user_id, timestamp
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 20

-- Find tasks due soon
SELECT title, assignee, due_date, status
FROM tasks
WHERE due_date BETWEEN NOW() AND NOW() + INTERVAL '3 days'
ORDER BY due_date

-- Join users and sessions
SELECT u.username, u.email, s.session_id, s.created_at
FROM users u
JOIN user_sessions s ON u.id = s.user_id
WHERE s.is_active = true
LIMIT 10
```

---

### 2. `sql_get_schema` - Get Database Schema
Get detailed schema information for tables including column names, types, constraints, and indexes.

**Endpoint**: `POST /tools/sql_get_schema`

**Parameters**:
- `table_name` (string, optional): Specific table to get schema for. If not provided, returns all tables.
- `include_indexes` (boolean, optional, default: false): Include index information

**Example Request - Single Table**:
```json
{
  "table_name": "users",
  "include_indexes": true
}
```

**Example Response**:
```json
{
  "success": true,
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "integer",
      "nullable": false,
      "default": "nextval('users_id_seq'::regclass)",
      "precision": 32,
      "constraint": "PRIMARY KEY"
    },
    {
      "name": "username",
      "type": "character varying",
      "nullable": false,
      "default": null,
      "max_length": 255,
      "constraint": "UNIQUE"
    },
    ...
  ],
  "indexes": {
    "users_pkey": {
      "type": "btree",
      "columns": ["id"]
    },
    "users_username_key": {
      "type": "btree",
      "columns": ["username"]
    }
  }
}
```

**Example Request - All Tables**:
```json
{}
```

**Example Response**:
```json
{
  "success": true,
  "tables": [
    {
      "name": "users",
      "description": "User accounts and authentication information",
      "column_count": 16
    },
    {
      "name": "documents",
      "description": "Document storage with full-text search and metadata",
      "column_count": 14
    },
    ...
  ],
  "table_count": 19
}
```

---

### 3. `sql_list_tables` - List All Tables
List all database tables with row counts, sizes, and descriptions.

**Endpoint**: `GET /tools/sql_list_tables`

**Parameters**: None

**Example Response**:
```json
{
  "success": true,
  "tables": [
    {
      "name": "users",
      "description": "User accounts and authentication information",
      "columns": 16,
      "size": "128 kB",
      "rows": 8
    },
    {
      "name": "documents",
      "description": "Document storage with full-text search and metadata",
      "columns": 14,
      "size": "192 kB",
      "rows": 10
    },
    {
      "name": "tasks",
      "description": "Task management and tracking",
      "columns": 12,
      "size": "96 kB",
      "rows": 5
    },
    ...
  ],
  "total_tables": 19
}
```

---

### 4. `sql_explain_query` - Explain Query Plan
Analyze a SQL query's execution plan for performance optimization.

**Endpoint**: `POST /tools/sql_explain_query`

**Parameters**:
- `query` (string, required): SQL query to explain

**Example Request**:
```json
{
  "query": "SELECT * FROM users WHERE email LIKE '%@ai-platform.com'"
}
```

**Example Response**:
```json
{
  "success": true,
  "query": "SELECT * FROM users WHERE email LIKE '%@ai-platform.com'",
  "execution_plan": [
    {
      "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "users",
        "Alias": "users",
        "Startup Cost": 0.00,
        "Total Cost": 22.50,
        "Plan Rows": 8,
        "Plan Width": 392,
        "Filter": "(email LIKE '%@ai-platform.com')"
      }
    }
  ]
}
```

---

## Security Features

### Query Validation
All SQL queries go through strict validation:

1. **Only SELECT queries allowed**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE` are blocked
2. **WITH...SELECT support**: Common Table Expressions (CTEs) are allowed
3. **No multiple statements**: Semicolons (except trailing) are blocked
4. **No dangerous keywords**: `EXEC`, `EXECUTE`, `GRANT`, `REVOKE` etc. are blocked

**Examples of Blocked Queries**:
```sql
-- ❌ Blocked: DROP TABLE
DROP TABLE users;

-- ❌ Blocked: UPDATE
UPDATE users SET role='admin' WHERE username='testuser1';

-- ❌ Blocked: DELETE
DELETE FROM users WHERE id=1;

-- ❌ Blocked: Multiple statements
SELECT * FROM users; DROP TABLE users;

-- ✅ Allowed: SELECT only
SELECT * FROM users WHERE is_active=true;

-- ✅ Allowed: WITH...SELECT (CTE)
WITH active_users AS (
  SELECT id, username FROM users WHERE is_active=true
)
SELECT * FROM active_users;
```

### Automatic LIMIT
If a query doesn't include a LIMIT clause, one is automatically added (default: 100 rows) to prevent accidental large data exports.

### Statement Timeout
Queries have a configurable timeout (default: 30 seconds) to prevent long-running queries from affecting system performance.

### Connection Pooling
All queries use connection pooling to efficiently manage database connections.

---

## Database Schema Reference

### Main Tables

#### `users` - User Accounts
```
id: integer (PK)
username: varchar(255) UNIQUE
email: varchar(255) UNIQUE
full_name: varchar(255)
role: varchar(50) DEFAULT 'user'
is_active: boolean DEFAULT true
created_at: timestamp
updated_at: timestamp
password_hash: varchar(255)
provider: varchar(50) DEFAULT 'local'
last_login: timestamp
```

#### `documents` - Document Storage
```
id: integer (PK)
title: varchar(255)
content: text
category: varchar(100)
tags: text[]
document_type: varchar(50)
file_path: varchar(500)
file_size: integer
uploaded_by: integer (FK -> users.id)
created_at: timestamp
updated_at: timestamp
metadata: jsonb
search_vector: tsvector
status: varchar(50)
```

#### `tasks` - Task Management
```
id: integer (PK)
title: varchar(255)
description: text
assignee: varchar(255)
status: varchar(50) DEFAULT 'pending'
priority: varchar(50) DEFAULT 'medium'
due_date: timestamp
created_by: varchar(255)
created_at: timestamp
updated_at: timestamp
completed_at: timestamp
metadata: jsonb
```

#### `audit_logs` - System Audit Trail
```
id: integer (PK)
action: varchar(255)
resource: varchar(255)
resource_id: varchar(255)
user_id: varchar(255)
details: jsonb
ip_address: varchar(50)
timestamp: timestamp
session_id: varchar(255)
```

#### `user_sessions` - User Sessions
```
id: integer (PK)
user_id: integer (FK -> users.id)
session_id: varchar(255)
ip_address: varchar(50)
user_agent: text
is_active: boolean DEFAULT true
created_at: timestamp
```

---

## Usage Workflow for Agents

### Recommended Workflow

1. **Discover Tables**
   ```
   First, use sql_list_tables to see what tables are available
   ```

2. **Inspect Schema**
   ```
   Use sql_get_schema to understand table structure before querying
   ```

3. **Write Query**
   ```
   Write SELECT query based on schema information
   ```

4. **Execute Query**
   ```
   Use sql_query to execute and get results
   ```

5. **Optimize if Needed**
   ```
   Use sql_explain_query to analyze performance
   ```

### Agent Prompt Example

```
When a user asks for database information:

1. First check what tables exist using sql_list_tables
2. If you need to know the table structure, use sql_get_schema
3. Write a SELECT query to get the requested data
4. Execute the query using sql_query
5. Present the results in a clear, formatted way

Example:
User: "Show me the most recent users"