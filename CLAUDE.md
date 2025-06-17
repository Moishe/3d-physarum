# Writing code

- We prefer simple, clean, maintainable solutions over clever or complex ones, even if the latter are more concise or performant. Readability and maintainability are primary concerns.
- Make the smallest reasonable changes to get to the desired outcome. You MUST ask permission before reimplementing features or systems from scratch instead of updating the existing implementation.
- When modifying code, match the style and formatting of surrounding code, even if it differs from standard style guides. Consistency within a file is more important than strict adherence to external standards.
- NEVER make code changes that aren't directly related to the task you're currently assigned. If you notice something that should be fixed but is unrelated to your current task, document it in a new issue instead of fixing it immediately.
- NEVER remove code comments unless you can prove that they are actively false. Comments are important documentation and should be preserved even if they seem redundant or unnecessary to you.
- All code files should start with a brief 2 line comment explaining what the file does. Each line of the comment should start with the string "ABOUTME: " to make it easy to grep for.
- When writing comments, avoid referring to temporal context about refactors or recent changes. Comments should be evergreen and describe the code as it is, not how it evolved or was recently changed.
- NEVER implement a mock mode for testing or for any purpose. We always use real data and real APIs, never mock implementations.
- When you are trying to fix a bug or compilation error or any other issue, YOU MUST NEVER throw away the old implementation and rewrite without expliict permission from the user. If you are going to do this, YOU MUST STOP and get explicit permission from the user.
- NEVER name things as 'improved' or 'new' or 'enhanced', etc. Code naming should be evergreen. What is new today will be "old" someday.
- After successfully making a change that passes all tests, ask for confirmation and then create a commit with the changes and a brief (<10 word) commit message.

# Getting help

- ALWAYS ask for clarification rather than making assumptions.
- If you're having trouble with something, it's ok to stop and ask for help. Especially if it's something your human might be better at.

# Testing

- Tests MUST cover the functionality being implemented.
- NEVER ignore the output of the system or the tests - Logs and messages often contain CRITICAL information.
- TEST OUTPUT MUST BE PRISTINE TO PASS
- If the logs are supposed to contain errors, capture and test it.
- NO EXCEPTIONS POLICY: Under no circumstances should you mark any test type as "not applicable". Every project, regardless of size or complexity, MUST have unit tests, integration tests, AND end-to-end tests. If you believe a test type doesn't apply, you need the human to say exactly "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME"

# Project Setup

- Use `uv` for dependency management and running tests
- To add a dependency: `uv pip install <package>`
- To run tests: `uv run pytest`

## We practice TDD. That means:

- Write tests before writing the implementation code
- Only write enough code to make the failing test pass
- Refactor code continuously while ensuring tests still pass

### TDD Implementation Process

- Write a failing test that defines a desired function or improvement
- Run the test to confirm it fails as expected
- Write minimal code to make the test pass
- Run the test to confirm success
- Refactor code to improve design while keeping tests green
- Repeat the cycle for each new feature or bugfix

# Commit Changes

When you are done with a feature or bug fix, verify the code you created by following the instructions below. If the verification finds no issues, create a commit with the verified commit message.

# Code Verification

Before committing any changes, you MUST use this verification tool:

1. **verify_staged_changes**: Use when you've made changes locally and want to verify them before committing
   - Always use the most recent git commit as `relative_to`.
   - Stage all the relevant files.
   - Provide a meaningful commit message suggestion
   - Include relevant test files or dependent modules in `extra_file_context`

## Required Information

When calling the verify_staged_changes tool, always provide:
- **summarized_goal**: A clear, concise summary of what you're trying to accomplish
- **user_requests**: The exact, verbatim user requests that led to these changes. These MUST be the EXACT words the user used when requesting these changes; DO NOT summarize and DO NOT rewrite them.
- **extra_file_context**: Files that might be affected but aren't in the diff (tests, config files, etc.)
- **extra_context**: Any additional context that might be relevant for verification

## Example Usage

Before committing features or bug fixes:
```
I'll verify these changes before committing:
[Call verify_staged_changes with appropriate parameters]
```
