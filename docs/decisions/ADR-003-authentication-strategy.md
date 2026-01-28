# ADR-003: Authentication Strategy

## Status
Accepted

## Date
2025-XX-XX

## Context

We need authentication for the IP2A staff interface and future member portal. Requirements:
- Support internal users (staff, officers, admins)
- Support external users (members, stewards)
- Audit trail of who performed actions
- Session management
- Role-based access control

## Options Considered

### Option A: Session-based Authentication (Traditional)
- Server stores session in database/Redis
- Cookie-based identification
- Simple to implement
- Requires session storage infrastructure

### Option B: JWT (JSON Web Tokens)
- Stateless authentication
- Token contains user identity and roles
- No server-side session storage required
- Industry standard for APIs

### Option C: OAuth2 with External Provider
- Delegate auth to Google/Microsoft
- Less password management
- Dependency on external service
- May not suit all union members

## Decision

We will use **JWT-based authentication** with:
- Access tokens (15 minute expiry)
- Refresh tokens (7 day expiry, stored in database)
- Bcrypt password hashing
- Role-based middleware

## Consequences

### Positive
- Stateless API (easier to scale)
- Standard approach, well-documented
- Works with future mobile apps
- No session storage infrastructure needed

### Negative
- Token revocation requires refresh token tracking
- Slightly more complex than session cookies

### Risks
- JWT secret key compromise = full breach
- Mitigation: Rotate keys, use strong secrets, monitor for anomalies

## References
- See: docs/architecture/AUTHENTICATION_ARCHITECTURE.md
