# MCP Server Database Schema Documentation

## Overview

The MCP Server uses PostgreSQL as its primary database for storing users, documents, tasks, and audit logs. The schema is designed for enterprise AI platform operations with full-text search, JSON metadata storage, and comprehensive audit trails.

## Database Information

- **Database Name:** `ai_platform`
- **User:** `admin`
- **Host:** `postgres:5432` (Docker container)
- **Schema Version:** 1.0
- **Created:** 2025-10-16

## Tables

### 1. users

Stores user accounts and authentication information.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_users_email` - Email lookup
- `idx_users_username` - Username lookup
- `idx_users_role` - Role-based queries

**Current Data:** 5 users (admin, john_doe, jane_smith, bob_wilson, alice_chen)

---

### 2. documents

Document storage with full-text search capabilities and flexible metadata.

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    document_type VARCHAR(100),
    category VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    version INTEGER DEFAULT 1,
    is_published BOOLEAN DEFAULT false,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_documents_title` - Full-text search on title (GIN index)
- `idx_documents_content` - Full-text search on content (GIN index)
- `idx_documents_category` - Category filtering
- `idx_documents_author` - Author lookup
- `idx_documents_created` - Chronological sorting
- `idx_documents_metadata` - JSON queries (GIN index)

**Features:**
- Full-text search using PostgreSQL `to_tsvector`
- JSONB metadata for flexible document properties
- Array-based tagging system
- Version tracking
- View count analytics

**Current Data:** 10 documents covering tutorials, documentation, reports, and analysis

**Sample Document Categories:**
- technical (guides, documentation)
- security (policies, best practices)
- business (reports, strategy)
- product (proposals, features)

---

### 3. tasks

Task management and tracking system.

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(50) DEFAULT 'normal',
    assignee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    creator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_tasks_status` - Status filtering
- `idx_tasks_assignee` - Assignee lookup
- `idx_tasks_due_date` - Due date sorting
- `idx_tasks_created` - Chronological sorting

**Status Values:**
- `open` - Not started
- `in_progress` - Currently being worked on
- `completed` - Finished
- `cancelled` - Cancelled

**Priority Values:**
- `low`
- `normal`
- `high`
- `urgent`

**Current Data:** 5 tasks across various departments

---

### 4. audit_logs

System audit trail for compliance and security monitoring.

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_audit_logs_user` - User activity lookup
- `idx_audit_logs_action` - Action type filtering
- `idx_audit_logs_created` - Time-based queries
- `idx_audit_logs_resource` - Resource tracking (composite)

**Common Action Types:**
- `document_create`, `document_view`, `document_edit`
- `user_login`, `user_create`
- `task_create`, `task_update`
- `api_call`

**Features:**
- IP address tracking (INET type)
- User agent storage for device tracking
- JSONB details for flexible audit data
- Automatic timestamping

**Current Data:** 10 audit log entries

---

## Views

### active_tasks

Shows all non-completed tasks with user information.

```sql
CREATE OR REPLACE VIEW active_tasks AS
SELECT
    t.*,
    u.username as assignee_name,
    c.username as creator_name
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
LEFT JOIN users c ON t.creator_id = c.id
WHERE t.status NOT IN ('completed', 'cancelled');
```

### published_documents

Shows all published documents with author information.

```sql
CREATE OR REPLACE VIEW published_documents AS
SELECT
    d.*,
    u.username as author_name,
    u.email as author_email
FROM documents d
LEFT JOIN users u ON d.author_id = u.id
WHERE d.is_published = true;
```

---

## Triggers

### Automatic Timestamp Updates

All main tables have triggers to automatically update the `updated_at` field:

```sql
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Data Statistics

| Table      | Rows | Purpose                          |
|------------|------|----------------------------------|
| users      | 5    | User accounts                    |
| documents  | 10   | Knowledge base and documentation |
| tasks      | 5    | Active and completed tasks       |
| audit_logs | 10   | Security and compliance logs     |

---

## Usage Examples

### Full-Text Search on Documents

```sql
-- Search documents by content
SELECT id, title, ts_rank(to_tsvector('english', content), query) AS rank
FROM documents, to_tsquery('english', 'AI & platform') query
WHERE to_tsvector('english', content) @@ query
ORDER BY rank DESC
LIMIT 10;
```

### JSON Metadata Queries

```sql
-- Find documents with specific metadata
SELECT id, title, metadata->>'difficulty' as difficulty
FROM documents
WHERE metadata->>'difficulty' = 'beginner';
```

### Array Tag Queries

```sql
-- Find documents with specific tags
SELECT id, title, tags
FROM documents
WHERE 'tutorial' = ANY(tags);
```

### Audit Trail Queries

```sql
-- Get user activity for the last 24 hours
SELECT
    u.username,
    a.action_type,
    a.resource_type,
    a.created_at
FROM audit_logs a
JOIN users u ON a.user_id = u.id
WHERE a.created_at > NOW() - INTERVAL '24 hours'
ORDER BY a.created_at DESC;
```

---

## Schema Files

- **Schema Creation:** `/services/mcp-server/schema.sql`
- **Sample Data:** `/services/mcp-server/seed.sql`

### Running Schema Migration

```bash
# Create schema
docker compose exec -T postgres psql -U admin -d ai_platform < services/mcp-server/schema.sql

# Load sample data
docker compose exec -T postgres psql -U admin -d ai_platform < services/mcp-server/seed.sql
```

---

## Security Considerations

1. **Soft Deletes:** User references use `ON DELETE SET NULL` to preserve audit trails
2. **Indexing:** All sensitive queries are indexed for performance
3. **Audit Logging:** All critical operations are logged in `audit_logs`
4. **IP Tracking:** Network activity is logged using PostgreSQL INET type
5. **JSON Flexibility:** JSONB allows storing additional context without schema changes

---

## Performance Optimization

1. **GIN Indexes:** Used for full-text search and JSONB queries
2. **Composite Indexes:** Resource tracking uses multi-column indexes
3. **Partial Indexes:** Views use filtered queries for better performance
4. **Connection Pooling:** Database pool configured in application (2-10 connections)

---

## Future Enhancements

### Planned Features

1. **Vector Embeddings:**
   ```sql
   ALTER TABLE documents ADD COLUMN embedding vector(1536);
   CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
   ```

2. **Document Versions:**
   - Create `document_versions` table for full version history
   - Track changes with diffs

3. **Notifications:**
   - Add `notifications` table for in-app notifications
   - Link to tasks and documents

4. **File Attachments:**
   - Create `attachments` table
   - Support for multiple file types

---

**Last Updated:** 2025-10-16
**Schema Version:** 1.0
**Maintained By:** AI Platform Team
