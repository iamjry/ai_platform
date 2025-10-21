#!/bin/bash

# Command Logger Script
# Usage: ./log_command.sh "command description" "actual command" "result (optional)"

COMMAND_HISTORY="COMMAND_HISTORY.md"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)

if [ $# -lt 2 ]; then
    echo "Usage: $0 \"description\" \"command\" [\"result\"]"
    echo "Example: $0 \"Check service status\" \"docker-compose ps\" \"All services healthy\""
    exit 1
fi

DESCRIPTION=$1
COMMAND=$2
RESULT=${3:-""}

# Create entry
cat >> $COMMAND_HISTORY << EOF

### $DESCRIPTION
Date: $DATE $TIME

\`\`\`bash
$COMMAND
EOF

if [ -n "$RESULT" ]; then
    cat >> $COMMAND_HISTORY << EOF
# Result: $RESULT
EOF
fi

cat >> $COMMAND_HISTORY << EOF
\`\`\`

EOF

echo "✅ Command logged to $COMMAND_HISTORY"
echo "Description: $DESCRIPTION"
echo "Command: $COMMAND"
