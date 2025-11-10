#!/bin/bash

# Create directory structure for Next.js + Material Design 3 UI
echo "Creating Next.js project structure..."

# Main directories
mkdir -p src/app
mkdir -p src/components/layout
mkdir -p src/components/chat
mkdir -p src/components/agents
mkdir -p src/components/knowledge
mkdir -p src/components/settings
mkdir -p src/components/common
mkdir -p src/lib/api
mkdir -p src/lib/theme
mkdir -p src/lib/utils
mkdir -p src/hooks
mkdir -p src/stores
mkdir -p src/types
mkdir -p public/images
mkdir -p public/icons

# Create app router pages
mkdir -p src/app/chat
mkdir -p src/app/agents
mkdir -p src/app/knowledge
mkdir -p src/app/settings
mkdir -p src/app/api/health

echo "✅ Directory structure created successfully!"
echo ""
echo "Structure:"
echo "src/"
echo "├── app/          # Next.js App Router"
echo "├── components/   # React Components"
echo "├── lib/          # Libraries and utilities"
echo "├── hooks/        # Custom React hooks"
echo "├── stores/       # Zustand state management"
echo "└── types/        # TypeScript types"
echo ""
echo "public/"
echo "├── images/       # Static images"
echo "└── icons/        # Static icons"
