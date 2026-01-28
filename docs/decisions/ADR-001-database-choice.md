# ADR-001: Database Choice

## Status
Accepted

## Date
2025-XX-XX (Backfill with original decision date)

## Context

We need a relational database for the IP2A union management system. Requirements:
- ACID compliance for financial data integrity
- Support for complex queries (reporting)
- JSON support for flexible schemas
- Strong ecosystem and long-term support
- Runs well in Docker for development
- Reasonable hosting costs

## Options Considered

### Option A: PostgreSQL
- Industry standard for complex applications
- Excellent JSON support (JSONB)
- Strong typing and data integrity
- Extensive extension ecosystem
- Free and open source

### Option B: MySQL/MariaDB
- Popular, well-understood
- Good performance
- Less robust JSON support
- Fewer advanced features

### Option C: SQLite
- Zero configuration
- File-based (simple backups)
- Not suitable for concurrent web access
- Limited scalability

## Decision

We will use **PostgreSQL 16**.

## Consequences

### Positive
- Full ACID compliance protects financial/dues data
- JSONB allows flexible metadata storage
- Array types useful for multi-value fields
- Excellent SQLAlchemy support
- Large community for troubleshooting

### Negative
- Slightly more complex setup than SQLite
- Requires running database server

### Risks
- PostgreSQL major version upgrades can require migration
- Mitigation: Stay on LTS versions, test upgrades in dev first
