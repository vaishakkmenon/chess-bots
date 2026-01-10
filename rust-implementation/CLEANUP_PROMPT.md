# Code Cleanup Analysis Prompt

Use this prompt with Claude Code to identify unneeded code in the codebase.

---

## Prompt for Claude Code

```
I need you to analyze this Rust chess engine codebase and identify dead code,
unused features, and unnecessary complexity that can be removed.

## Context

This is a chess engine with:
- Move generation (perft-tested and working correctly)
- Alpha-beta search with iterative deepening
- Transposition table
- Material + PSQT evaluation
- Magic bitboards for move generation

The engine is working correctly but may have accumulated dead code,
experimental features, or unused alternatives during development.

## Analysis Tasks

### 1. Find Unused/Dead Code
- Unused imports
- Commented-out code that should be removed
- Unused functions or modules
- Dead code paths that are never executed
- Old implementations that have been superseded

### 2. Identify Redundant Implementations
- Multiple versions of the same functionality
- Archived/backup code that's no longer needed
- Test utilities that are unused

### 3. Find Incomplete Features
- Feature flags that don't work
- Half-implemented features
- TODO/FIXME comments indicating unfinished work

### 4. Identify Over-Engineering
- Abstractions that are only used once
- Overly complex code that could be simplified
- Dead code paths (unreachable code)

### 5. Check for Unused Dependencies
- Cargo dependencies that aren't actually used
- Imported modules that are never called

## Instructions

1. Read through the codebase systematically
2. Create a report identifying:
   - Dead code (unused functions, modules, imports)
   - Over-engineered abstractions that could be simplified
   - Duplicate functionality
   - Commented-out code that should be removed
   - Features or modules that are never used
   - Unused dependencies in Cargo.toml

3. For each finding, provide:
   - File location
   - Description of the unused/unneeded code
   - Whether it can be safely removed or if there's a reason to keep it
   - Estimated impact of removal (code clarity, compilation time, etc.)

4. Prioritize findings by impact:
   - High: Dead code that adds confusion
   - Medium: Commented-out code that should be removed
   - Low: Unused imports or minor cleanup

Please analyze the rust-implementation directory and create a comprehensive report.