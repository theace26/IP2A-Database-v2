#!/bin/bash
# Clean up expired email tokens and other session data
# Run daily via cron: 0 4 * * * /path/to/cleanup_sessions.sh

set -e

DB_HOST="${DB_HOST:-localhost}"
DB_NAME="${DB_NAME:-unioncore}"
DB_USER="${DB_USER:-postgres}"

echo "[$(date)] Starting session cleanup..."

# Delete expired email tokens (password reset, email verification)
DELETED_TOKENS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    DELETE FROM email_tokens
    WHERE expires_at < NOW()
    RETURNING id;
" | wc -l)

echo "[$(date)] Deleted $DELETED_TOKENS expired email tokens"

# Delete old password reset tokens (older than 1 week)
DELETED_OLD=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    DELETE FROM email_tokens
    WHERE created_at < NOW() - INTERVAL '7 days'
    AND token_type = 'password_reset'
    RETURNING id;
" 2>/dev/null | wc -l || echo "0")

echo "[$(date)] Deleted $DELETED_OLD old password reset tokens"

# Unlock users whose lock period has expired
UNLOCKED_USERS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    UPDATE users
    SET locked_until = NULL
    WHERE locked_until IS NOT NULL
    AND locked_until < NOW()
    RETURNING id;
" | wc -l)

echo "[$(date)] Unlocked $UNLOCKED_USERS users with expired locks"

echo "[$(date)] Session cleanup complete!"
