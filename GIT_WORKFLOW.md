# Git Workflow Guide

## Repository Information

**Repository**: AI Agents Platform
**Current Version**: v1.0.0
**Branch**: main
**Configured Email**: your-email@gmail.com

## Version Control Strategy

This project uses **Semantic Versioning** (SemVer):
- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Common Git Commands

### Check Status
```bash
git status
git log --oneline
git tag -l
```

### Create a New Feature Branch
```bash
git checkout -b feature/new-feature-name
# Make changes...
git add .
git commit -m "feat: add new feature description"
git checkout main
git merge feature/new-feature-name
```

### Make Changes and Commit
```bash
# Stage specific files
git add file1.py file2.py

# Or stage all changes
git add .

# Commit with message
git commit -m "type: description

Detailed explanation of changes
- Change 1
- Change 2"
```

### Commit Message Types
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Adding or updating tests
- `chore:` Maintenance tasks
- `build:` Build system changes
- `ci:` CI/CD changes

### Create a New Version Tag

**For Patch Release (1.0.0 → 1.0.1)**
```bash
# Update VERSION file
echo "1.0.1" > VERSION

# Commit version bump
git add VERSION
git commit -m "chore: bump version to 1.0.1"

# Create annotated tag
git tag -a v1.0.1 -m "Release v1.0.1

Bug Fixes:
- Fixed issue #1
- Fixed issue #2"
```

**For Minor Release (1.0.0 → 1.1.0)**
```bash
echo "1.1.0" > VERSION
git add VERSION
git commit -m "chore: bump version to 1.1.0"

git tag -a v1.1.0 -m "Release v1.1.0

New Features:
- Feature 1
- Feature 2"
```

**For Major Release (1.0.0 → 2.0.0)**
```bash
echo "2.0.0" > VERSION
git add VERSION
git commit -m "chore: bump version to 2.0.0"

git tag -a v2.0.0 -m "Release v2.0.0

Breaking Changes:
- Breaking change 1
- Breaking change 2

New Features:
- Feature 1"
```

### View Version History
```bash
# List all tags
git tag -l

# Show tag details
git show v1.0.0

# List commits since last tag
git log v1.0.0..HEAD --oneline

# View commits between tags
git log v1.0.0..v1.1.0 --oneline
```

### Undo Changes

**Undo unstaged changes**
```bash
git checkout -- file.py
```

**Undo staged changes**
```bash
git reset HEAD file.py
```

**Undo last commit (keep changes)**
```bash
git reset --soft HEAD~1
```

**Undo last commit (discard changes)**
```bash
git reset --hard HEAD~1
```

### View Changes
```bash
# See unstaged changes
git diff

# See staged changes
git diff --staged

# See changes in specific file
git diff path/to/file.py

# Compare branches
git diff main..feature-branch
```

## Remote Repository Setup

### Add GitHub/GitLab Remote
```bash
# GitHub
git remote add origin git@github.com:username/ai_platform.git

# Or GitLab
git remote add origin git@gitlab.com:username/ai_platform.git

# Verify remote
git remote -v
```

### Push to Remote
```bash
# First push
git push -u origin main

# Push tags
git push --tags

# Or push everything
git push origin main --tags
```

### Pull from Remote
```bash
git pull origin main
```

## Branch Strategy

### Main Branch
- `main`: Production-ready code
- Always stable and deployable
- Protected branch (requires PR for changes)

### Development Branches
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes
- `release/*`: Release preparation

### Example Workflow
```bash
# Create feature branch
git checkout -b feature/pdf-enhancements

# Work on feature...
git add .
git commit -m "feat: enhance PDF processing with OCR"

# Switch back to main
git checkout main

# Merge feature
git merge feature/pdf-enhancements

# Delete feature branch
git branch -d feature/pdf-enhancements
```

## .gitignore Coverage

The following are automatically ignored:
- ✅ `.env` files (API keys, secrets)
- ✅ `__pycache__/` and `*.pyc`
- ✅ Docker volumes (postgres_data, redis_data, etc.)
- ✅ IDE files (.vscode, .idea)
- ✅ Logs (*.log)
- ✅ Virtual environments (venv/, env/)
- ✅ Database files (*.db, *.sqlite)
- ✅ Model files (*.bin, *.pt)

## Best Practices

1. **Commit Often**: Make small, focused commits
2. **Write Clear Messages**: Explain what and why, not how
3. **Test Before Commit**: Ensure code works
4. **Review Changes**: Use `git diff` before committing
5. **Tag Releases**: Create tags for all releases
6. **Update VERSION**: Keep VERSION file in sync with tags
7. **Never Commit Secrets**: Check .gitignore before committing
8. **Use Branches**: Don't work directly on main for big changes

## Emergency Recovery

### Lost Changes
```bash
# View reflog (history of HEAD movements)
git reflog

# Restore to previous state
git reset --hard HEAD@{N}
```

### Restore Deleted File
```bash
# Find commit where file existed
git log -- path/to/file.py

# Restore file
git checkout <commit-hash> -- path/to/file.py
```

## Version History

| Version | Date       | Description                          |
|---------|------------|--------------------------------------|
| v1.0.0  | 2025-10-21 | Initial release with full platform   |

## Useful Aliases (Optional)

Add to `~/.gitconfig`:
```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = log --graph --oneline --all
```

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
