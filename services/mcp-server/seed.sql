-- MCP Server Database Seed Data
-- Sample data for testing and development

-- Insert sample users
INSERT INTO users (username, email, full_name, role) VALUES
('admin', 'admin@example.com', 'System Administrator', 'admin'),
('john_doe', 'john.doe@example.com', 'John Doe', 'user'),
('jane_smith', 'jane.smith@example.com', 'Jane Smith', 'user'),
('bob_wilson', 'bob.wilson@example.com', 'Bob Wilson', 'manager'),
('alice_chen', 'alice.chen@example.com', 'Alice Chen', 'user')
ON CONFLICT (username) DO NOTHING;

-- Insert sample documents
INSERT INTO documents (title, content, summary, document_type, category, author_id, is_published, metadata, tags) VALUES
(
    'Getting Started with AI Platform',
    'This comprehensive guide walks you through the setup and configuration of the AI Platform. The platform provides enterprise-grade AI capabilities including natural language processing, document analysis, and intelligent automation. Key features include: 1) Multi-model support for various AI tasks, 2) Secure data handling and compliance, 3) Scalable architecture for enterprise workloads, 4) Integration with existing business systems. To get started, follow the installation instructions in the next section.',
    'Complete setup guide for the AI Platform with installation instructions and key features overview.',
    'guide',
    'technical',
    1,
    true,
    '{"difficulty": "beginner", "estimated_time": "30 minutes", "version": "2.0"}',
    ARRAY['tutorial', 'setup', 'getting-started']
),
(
    'API Reference Documentation',
    'Complete API reference for the MCP Server. The server provides 28 different tools across multiple categories including data analysis, search, content generation, security, and more. Each endpoint accepts JSON payloads and returns structured responses. Authentication is required for most endpoints using Bearer tokens. Rate limiting is applied at 100 requests per minute per user. All endpoints support both synchronous and asynchronous operations.',
    'API documentation covering all 28 tools and authentication requirements.',
    'documentation',
    'technical',
    1,
    true,
    '{"api_version": "2.0", "last_updated": "2025-10-16"}',
    ARRAY['api', 'reference', 'documentation']
),
(
    'Security Best Practices',
    'Security is paramount when deploying AI systems. This document outlines best practices for securing your AI Platform deployment. Topics covered include: authentication and authorization, data encryption at rest and in transit, audit logging and compliance, secure API key management, network security and firewall configuration, regular security updates and patches, incident response procedures, and data privacy considerations including GDPR and CCPA compliance.',
    'Comprehensive security guidelines for AI Platform deployment and operations.',
    'policy',
    'security',
    4,
    true,
    '{"compliance": ["GDPR", "CCPA", "SOC2"], "review_date": "2025-07-01"}',
    ARRAY['security', 'compliance', 'best-practices']
),
(
    'Data Analysis Tools Guide',
    'The platform provides powerful data analysis tools for processing and visualizing enterprise data. Tools include statistical analysis, CSV processing with pandas, chart generation, and metric calculations. This guide demonstrates how to use each tool with practical examples. You can analyze sales data, generate financial reports, process customer data, and create interactive visualizations. The tools support various data formats including CSV, JSON, and Excel.',
    'Guide to data analysis and visualization tools with practical examples.',
    'guide',
    'technical',
    2,
    true,
    '{"tools_covered": ["analyze_data", "process_csv", "generate_chart", "calculate_metrics"]}',
    ARRAY['data-analysis', 'visualization', 'tutorial']
),
(
    'Q4 Business Strategy Report',
    'Executive summary of Q4 business strategy and objectives. Our focus for Q4 includes: expanding into new markets, launching three new product features, improving customer satisfaction scores by 15%, reducing operational costs by 10%, and growing revenue by 25% year-over-year. Key initiatives include AI-driven customer support, automated workflow optimization, enhanced security features, and strategic partnerships with major enterprise clients. Budget allocation prioritizes R&D and customer success.',
    'Q4 strategy focusing on market expansion and product development.',
    'report',
    'business',
    4,
    true,
    '{"quarter": "Q4", "year": 2025, "confidential": false}',
    ARRAY['strategy', 'business', 'quarterly']
),
(
    'Customer Feedback Analysis',
    'Analysis of customer feedback from the past quarter reveals several key insights. Overall satisfaction score is 4.2/5.0, with particularly high marks for platform reliability (4.5/5) and customer support (4.4/5). Areas for improvement include: documentation clarity (3.8/5), onboarding process (3.9/5), and API response times (4.0/5). Common feature requests include: more language support, enhanced visualization options, better Excel integration, and mobile app development.',
    'Q3 customer feedback summary with satisfaction scores and improvement areas.',
    'analysis',
    'business',
    3,
    true,
    '{"period": "Q3 2025", "responses": 1247, "avg_score": 4.2}',
    ARRAY['feedback', 'customer', 'analysis']
),
(
    'Machine Learning Model Comparison',
    'Comparative analysis of various machine learning models for document classification tasks. We evaluated BERT, GPT-3.5, Claude, and Qwen2.5 across multiple metrics. Results show: BERT achieved 92% accuracy with 150ms average latency, GPT-3.5 scored 95% accuracy with 800ms latency, Claude reached 96% accuracy with 600ms latency, and Qwen2.5 delivered 94% accuracy with 200ms latency. For cost-effectiveness and speed, Qwen2.5 is recommended for production use.',
    'ML model comparison for document classification with performance metrics.',
    'analysis',
    'technical',
    5,
    true,
    '{"models_tested": 4, "test_dataset_size": 10000, "evaluation_date": "2025-10-01"}',
    ARRAY['machine-learning', 'comparison', 'performance']
),
(
    'Integration Guide: Slack & Teams',
    'Step-by-step guide for integrating the AI Platform with Slack and Microsoft Teams. The integration allows you to receive notifications, trigger workflows, and query the AI assistant directly from your chat applications. Configuration requires: 1) Creating app credentials in Slack/Teams admin panels, 2) Adding webhook URLs to platform settings, 3) Configuring notification preferences, 4) Testing the integration with sample messages. Includes troubleshooting tips for common issues.',
    'Integration instructions for Slack and Microsoft Teams with configuration steps.',
    'guide',
    'integration',
    2,
    true,
    '{"platforms": ["slack", "teams"], "difficulty": "intermediate"}',
    ARRAY['integration', 'slack', 'teams', 'tutorial']
),
(
    'Financial Calculations Guide',
    'The financial calculator tool supports multiple operations including ROI (Return on Investment), NPV (Net Present Value), and IRR (Internal Rate of Return) calculations. This guide explains each calculation method, provides formulas, and demonstrates real-world examples. ROI calculation: (Gain - Cost) / Cost × 100. NPV uses discounted cash flow analysis. IRR finds the rate where NPV equals zero. Examples include project evaluation, investment analysis, and cost-benefit studies.',
    'Guide to financial calculations including ROI, NPV, and IRR with examples.',
    'guide',
    'business',
    4,
    true,
    '{"calculation_types": ["ROI", "NPV", "IRR"], "examples_included": true}',
    ARRAY['finance', 'calculations', 'tutorial']
),
(
    'Draft: New Feature Proposal',
    'Proposal for implementing real-time collaboration features in the document editor. This would allow multiple users to edit documents simultaneously with live updates. Technical requirements include WebSocket connections, operational transform algorithms for conflict resolution, presence indicators, and change tracking. Estimated development time: 8 weeks. Budget: $80,000. Expected impact: 30% increase in user engagement.',
    'Proposal for real-time collaboration features (draft)',
    'proposal',
    'product',
    3,
    false,
    '{"status": "draft", "priority": "high", "budget": 80000}',
    ARRAY['feature', 'collaboration', 'draft']
);

-- Insert sample tasks
INSERT INTO tasks (title, description, status, priority, assignee_id, creator_id, due_date, metadata) VALUES
(
    'Review Q4 Financial Report',
    'Comprehensive review of Q4 financial performance including revenue analysis, expense breakdown, and profitability metrics. Prepare summary for executive team.',
    'open',
    'high',
    4,
    1,
    CURRENT_TIMESTAMP + INTERVAL '7 days',
    '{"department": "finance", "estimated_hours": 8}'
),
(
    'Update API Documentation',
    'Update API reference documentation to reflect the new 28 tools added in version 2.0. Include request/response examples for each endpoint.',
    'in_progress',
    'high',
    2,
    1,
    CURRENT_TIMESTAMP + INTERVAL '3 days',
    '{"department": "engineering", "estimated_hours": 12}'
),
(
    'Customer Feedback Analysis',
    'Analyze customer feedback from the past month and identify top 5 feature requests. Prepare presentation for product team meeting.',
    'open',
    'normal',
    3,
    4,
    CURRENT_TIMESTAMP + INTERVAL '5 days',
    '{"department": "product", "estimated_hours": 6}'
),
(
    'Security Audit',
    'Conduct comprehensive security audit of all API endpoints. Check for vulnerabilities, update security policies, and generate compliance report.',
    'open',
    'high',
    5,
    1,
    CURRENT_TIMESTAMP + INTERVAL '14 days',
    '{"department": "security", "estimated_hours": 20}'
),
(
    'Setup Monitoring Dashboards',
    'Create Grafana dashboards for monitoring system health, API performance, and error rates. Configure alerts for critical metrics.',
    'in_progress',
    'normal',
    2,
    1,
    CURRENT_TIMESTAMP + INTERVAL '2 days',
    '{"department": "devops", "estimated_hours": 4}'
);

-- Insert sample audit logs
INSERT INTO audit_logs (user_id, action_type, resource_type, resource_id, details, ip_address) VALUES
(1, 'document_create', 'document', '1', '{"title": "Getting Started with AI Platform", "action": "created"}', '192.168.1.100'),
(2, 'document_view', 'document', '1', '{"action": "viewed", "duration": 120}', '192.168.1.101'),
(3, 'document_edit', 'document', '4', '{"action": "edited", "changes": ["content", "metadata"]}', '192.168.1.102'),
(4, 'user_login', 'user', '4', '{"action": "login", "success": true}', '192.168.1.103'),
(2, 'task_create', 'task', '2', '{"title": "Update API Documentation", "assigned_to": "john_doe"}', '192.168.1.101'),
(5, 'api_call', 'tool', 'analyze_data', '{"action": "executed", "duration_ms": 450}', '192.168.1.104'),
(3, 'document_view', 'document', '5', '{"action": "viewed", "duration": 90}', '192.168.1.102'),
(1, 'user_create', 'user', '5', '{"username": "alice_chen", "role": "user"}', '192.168.1.100'),
(4, 'task_update', 'task', '1', '{"action": "status_changed", "old_status": "open", "new_status": "in_progress"}', '192.168.1.103'),
(2, 'api_call', 'tool', 'generate_report', '{"action": "executed", "duration_ms": 1200}', '192.168.1.101');

-- Update view counts for documents
UPDATE documents SET view_count = 156 WHERE id = 1;
UPDATE documents SET view_count = 89 WHERE id = 2;
UPDATE documents SET view_count = 234 WHERE id = 3;
UPDATE documents SET view_count = 45 WHERE id = 4;
UPDATE documents SET view_count = 178 WHERE id = 5;
UPDATE documents SET view_count = 67 WHERE id = 6;
UPDATE documents SET view_count = 92 WHERE id = 7;
UPDATE documents SET view_count = 34 WHERE id = 8;
UPDATE documents SET view_count = 123 WHERE id = 9;
UPDATE documents SET view_count = 12 WHERE id = 10;

-- Verify data insertion
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Documents', COUNT(*) FROM documents
UNION ALL
SELECT 'Tasks', COUNT(*) FROM tasks
UNION ALL
SELECT 'Audit Logs', COUNT(*) FROM audit_logs;
