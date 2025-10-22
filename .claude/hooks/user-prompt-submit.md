# Pre-Submit Hook: Version Control & Efficiency Reminder

## 🔴 CRITICAL: Version Control Best Practices

**Commit Strategy - Logical Units:**
- Commit when a **logical unit of work** is complete
- Commit when a **feature/fix/refactor** is done
- Commit **before risky changes** (so you can revert)
- Commit **after testing** passes
- Group **related changes** together in one commit

**Examples of Good Commits:**
- ✅ "Add PDF upload feature with validation"
- ✅ "Fix context limit calculation bug"
- ✅ "Refactor model selection to use dropdown"
- ✅ "Update i18n with Vietnamese translations"

**Examples of Bad Commits:**
- ❌ "Change one variable name"
- ❌ "Fix typo"
- ❌ "Work in progress"

**When to Commit:**
1. Before starting risky/experimental work
2. After completing a feature/fix
3. Before switching tasks
4. When tests pass
5. End of work session

## 💰 Token Efficiency Rules

### 1. Search Before Reading
- Use `Grep` to find specific patterns: `grep "function_name"`
- Use `Glob` to find files: `glob "**/*.py"`
- Only `Read` full files when absolutely needed
- Use `Read` with `offset/limit` for large files

### 2. Batch Operations
- Make multiple file edits in one message
- Run parallel bash commands: `cmd1 && cmd2 && cmd3`
- Run multiple tool calls simultaneously when independent
- Example: Read 3 related files at once, not one by one

### 3. Avoid Repetition
- Reference code by location: `file.py:123-145`
- Use `git diff` to show changes, not full files
- Don't repeat context already in conversation
- Use variables/patterns for similar operations

### 4. Smart Tool Selection
- `Task` agent for complex multi-step work
- `Edit` for precise changes (not rewriting files)
- `Grep` instead of `Read` + manual search
- `Glob` instead of `find` commands
- Specialized tools over bash when possible

### 5. Minimize Context Usage
- Read file sections, not entire files
- Use `-C 5` in grep for 5 lines context
- Use `head -n 50` or `tail -n 50` for previews
- Check file size before reading: `ls -lh file.py`

### 6. Reuse and Organize
- Create helper functions for repeated tasks
- Use templates for similar operations
- Reference previous successful patterns
- Build on existing code, don't rewrite

**User Expectation:** High efficiency, minimal token waste, meaningful commits
