---
inclusion: auto
---

# Everything Claude Code - Best Practices

This project follows the battle-tested practices from the everything-claude-code repository (50k+ stars, Anthropic Hackathon Winner).

## Core Principles

### Code Quality
- Write tests first (TDD methodology)
- Maintain 80%+ test coverage
- Use immutable data structures by default
- Follow language-specific idioms and best practices
- Security-first mindset (OWASP Top 10 awareness)

### Development Workflow
1. **Plan First**: Break down features into clear implementation steps
2. **Test-Driven Development**: Write failing tests before implementation
3. **Incremental Implementation**: Small, focused commits
4. **Code Review**: Self-review before considering complete
5. **Documentation**: Keep docs in sync with code changes

### Performance & Token Optimization
- Use appropriate model for task complexity (Haiku for simple, Sonnet for standard, Opus for complex)
- Clear context between unrelated tasks
- Compact at logical breakpoints (after research, before implementation)
- Monitor token usage with cost awareness

### Language-Specific Guidelines

#### TypeScript/JavaScript
- Prefer functional patterns and immutability
- Use TypeScript strict mode
- Implement proper error handling
- Follow React/Next.js best practices for frontend

#### Python
- Follow PEP 8 style guide
- Use type hints consistently
- Leverage Python idioms (list comprehensions, context managers)
- Implement proper exception handling

#### Go
- Follow Go idioms and conventions
- Use interfaces for abstraction
- Implement proper error handling (no panic in libraries)
- Write table-driven tests

### Security Practices
- Never commit secrets or API keys
- Validate and sanitize all inputs
- Use parameterized queries for database operations
- Implement proper authentication and authorization
- Regular security audits

### API Design
- RESTful conventions
- Proper HTTP status codes
- Consistent error response format
- Pagination for list endpoints
- Versioning strategy

### Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical user flows
- Property-based testing for complex logic
- Maintain test isolation

## Project Structure
- Keep files focused and single-purpose
- Organize by feature, not by type
- Separate concerns (business logic, data access, presentation)
- Use clear, descriptive naming

## Git Workflow
- Atomic commits with clear messages
- Feature branches for new work
- PR reviews before merging
- Keep main branch deployable

## References
- Full repo: https://github.com/affaan-m/everything-claude-code
- Skills installed in: ~/.kiro/skills/
- Rules installed in: ~/.claude/rules/
