#!/bin/bash

# Secret Checker Script
# Run this before pushing to any remote repository

echo "🔐 Security Check: Scanning for Secrets"
echo "========================================"
echo ""

ISSUES_FOUND=0

# Check if .env is tracked
echo "1️⃣ Checking if .env file is tracked..."
if git ls-files | grep -q "^\.env$"; then
    echo "❌ DANGER: .env file is tracked by git!"
    echo "   Run: git rm --cached .env"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ .env is not tracked (good!)"
fi
echo ""

# Check if .env exists and is ignored
echo "2️⃣ Verifying .env is in .gitignore..."
if grep -q "^\.env$" .gitignore; then
    echo "✅ .env is in .gitignore"
else
    echo "⚠️  WARNING: .env not found in .gitignore"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# Check for hardcoded API keys patterns
echo "3️⃣ Scanning for hardcoded API keys..."
API_KEY_PATTERN='(OPENAI|ANTHROPIC|GEMINI|GOOGLE)_API_KEY.*[:=].*["\x27][sk|api]-[a-zA-Z0-9]{20,}'

if git ls-files | xargs grep -E "$API_KEY_PATTERN" 2>/dev/null; then
    echo "❌ DANGER: Found hardcoded API keys!"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No hardcoded API keys found"
fi
echo ""

# Check for password patterns (excluding documentation and examples)
echo "4️⃣ Scanning for hardcoded passwords..."
PASSWORD_PATTERN='password.*[:=].*["\x27][^"\x27$]{8,}'

# Exclude common false positives: .example files, .md docs, default values, env vars
SUSPICIOUS=$(git ls-files | xargs grep -iE "$PASSWORD_PATTERN" 2>/dev/null | \
    grep -v "\.env\.example" | \
    grep -v "\.md:" | \
    grep -v "PASSWORD}" | \
    grep -v "POSTGRES_PASSWORD" | \
    grep -v "SMTP_PASSWORD" | \
    grep -v "REDIS_PASSWORD" | \
    grep -v "RABBITMQ" | \
    grep -v "os.getenv" | \
    grep -v "os.environ" | \
    grep -v "getenv.*PASSWORD" | \
    grep -v "password@postgres" | \
    grep -v "\"Password\"" | \
    grep -v "\"Mật khẩu\"" | \
    grep -v "# Your" | \
    grep -v "EXAMPLE")

if [ -n "$SUSPICIOUS" ]; then
    echo "$SUSPICIOUS"
    echo "⚠️  WARNING: Possible hardcoded passwords found"
    echo "   Review the above matches carefully"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No hardcoded passwords found (checked real code, not docs/examples)"
fi
echo ""

# Check for AWS keys
echo "5️⃣ Scanning for AWS credentials..."
AWS_PATTERN='(AWS|aws).*[:=].*["\x27][A-Z0-9]{20}'

if git ls-files | xargs grep -E "$AWS_PATTERN" 2>/dev/null; then
    echo "⚠️  WARNING: Possible AWS credentials found"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No AWS credentials found"
fi
echo ""

# Check for private keys
echo "6️⃣ Checking for private key files..."
if git ls-files | grep -E '\.(pem|key|p12|pfx)$'; then
    echo "❌ DANGER: Private key files are tracked!"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No private key files tracked"
fi
echo ""

# List all tracked config files
echo "7️⃣ Tracked configuration files:"
git ls-files | grep -E '(config|\.env|\.yaml|\.yml|\.conf|\.ini)$' | while read file; do
    echo "   📄 $file"
done
echo ""

# Check for database credentials
echo "8️⃣ Checking for database credentials..."
DB_PATTERN='(postgres|mysql|mongodb):\/\/[^:]+:[^@]+@'

if git ls-files | xargs grep -E "$DB_PATTERN" 2>/dev/null; then
    echo "⚠️  WARNING: Possible database credentials in connection strings"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No database credentials found"
fi
echo ""

# Summary
echo "========================================"
echo "📊 Security Check Summary"
echo "========================================"
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ ✅ ✅  ALL CHECKS PASSED  ✅ ✅ ✅"
    echo ""
    echo "Your repository appears safe to push!"
    echo ""
    echo "Recommendations:"
    echo "  1. Use a PRIVATE repository"
    echo "  2. Review all configuration files manually"
    echo "  3. Double-check .env is not tracked"
    echo "  4. Consider using git-secrets for additional protection"
    echo ""
    exit 0
else
    echo "❌ ❌ ❌  ISSUES FOUND: $ISSUES_FOUND  ❌ ❌ ❌"
    echo ""
    echo "⚠️  DO NOT PUSH TO REMOTE REPOSITORY ⚠️"
    echo ""
    echo "Fix the issues above before pushing!"
    echo ""
    exit 1
fi
