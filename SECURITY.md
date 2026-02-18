# Security Features

Cheese Brain implements multiple layers of security to protect your knowledge base.

## 🔒 File Permissions

**Automatic:** Database and backup files are automatically secured with owner-only permissions (`0600`).

- `~/.cheese-brain/` directory: `0700` (owner-only)
- `cheese-brain.duckdb`: `0600` (owner read/write only)
- All export/backup files: `0600`

This prevents other users or processes on your system from reading your knowledge base.

## 🏷️ Sensitive Field Redaction

**Automatic:** Fields matching sensitive patterns are redacted in CLI output.

Sensitive patterns include:
- `password`, `passwd`
- `secret`
- `api_key`, `api-key`
- `token`
- `private_key`, `private-key`
- `auth`, `credential`
- `bearer`, `jwt`

**Example:**
```bash
# Default: sensitive values redacted
$ cheese-brain get abc-123
Data:
{
  "url": "https://api.example.com",
  "api_key": "●●●●●●●●",
  "timeout": 30
}

# Show real values with --reveal flag
$ cheese-brain get abc-123 --reveal
Data:
{
  "url": "https://api.example.com",
  "api_key": "sk-example-abc123...",
  "timeout": 30
}
```

Redaction applies to:
- `cheese-brain get` (table and JSON output)
- `cheese-brain search --format json`
- `cheese-brain fts --format json`

**Database and exports are NOT redacted** - this is display-only protection.

## 🔐 Encrypted Backups

**Optional:** Encrypt export files with a passphrase.

```bash
# Export with encryption
$ cheese-brain export backup.json --encrypt
Encryption passphrase: ********
Confirm passphrase: ********
✅ Exported and encrypted 107 entities to backup.json

# Restore encrypted backup (auto-detected)
$ cheese-brain restore-backup backup.json
🔒 Encrypted backup detected
Decryption passphrase: ********
✅ Decryption successful
✅ Imported 107 entities from backup.json
```

**Encryption details:**
- Algorithm: Fernet (AES-128 in CBC mode with HMAC)
- Key derivation: PBKDF2-SHA256 (600,000 iterations)
- Random 16-byte salt per file
- Encrypted files have header: `CHEESE_BRAIN_ENCRYPTED_V1`

**When to use encryption:**
- Syncing backups to cloud storage (Dropbox, iCloud, etc.)
- Storing backups on USB drives
- Sharing backups across machines

## 🛡️ Data Validation

**Automatic:** Entity data is validated before storage.

**Size limit:** 1MB per entity's `data` field
- Prevents database bloat
- Catches accidental bulk imports

**Nesting limit:** 10 levels max
- Prevents recursion issues
- Ensures serialization stability

**Example error:**
```bash
$ cheese-brain add --title "Huge Doc" --category tool \
  --data '{"content": "<100MB of text>"}'
❌ Error: Data field too large: 102400.0KB (max 1024KB)
```

## 🔍 SQL Injection Protection

**Automatic:** All database queries use parameterized statements.

```python
# Safe (parameterized)
results = conn.execute("""
    SELECT * FROM entities WHERE title ILIKE ?
""", [f"%{query}%"])

# Never used (f-string interpolation)
# results = conn.execute(f"SELECT * FROM entities WHERE title ILIKE '%{query}%'")
```

## 📋 Security Checklist

**For personal use:**
- ✅ File permissions protect against local snooping
- ✅ Sensitive field redaction prevents terminal leaks
- ✅ No authentication needed (single-user, local-only)

**For cloud-synced backups:**
- ✅ Use `--encrypt` flag on exports
- ✅ Store passphrase in password manager (not in Cheese Brain!)
- ✅ Test restore process before disaster strikes

**For shared systems:**
- ✅ Use separate user accounts (OS-level isolation)
- ✅ Encrypt sensitive entities with external tools (GPG, age)
- ✅ Consider full-disk encryption (FileVault, LUKS)

## ⚠️ What Cheese Brain Does NOT Protect Against

- **Malware with your user permissions:** If malware runs as you, it can read your database (same as any file)
- **Root/admin access:** Users with root can read anything
- **Physical access:** Unencrypted disk = readable database
- **Memory dumps:** Database is decrypted in RAM during use
- **Screen recording:** Terminal output can be captured

**Mitigation:**
- Use full-disk encryption (FileVault, BitLocker, LUKS)
- Lock your screen when away
- Don't store highly sensitive secrets in plain text (use secret managers like 1Password, Bitwarden)
- Encrypt backups that leave your machine

## 🔒 Best Practices

### Storing Secrets

**DON'T store in plain text:**
```json
{
  "api_key": "sk-example-abc123...",
  "password": "my-password-123"
}
```

**DO use secret managers:**
```json
{
  "api_key_location": "1Password: OpenAI API Key",
  "notes": "Retrieve key from password manager"
}
```

Or reference environment variables:
```json
{
  "api_key": "ENV:OPENAI_API_KEY",
  "notes": "Set via export OPENAI_API_KEY=..."
}
```

### Backup Strategy

1. **Daily automated backups** (plain text, local)
   - Fast recovery
   - Good for accidental deletions

2. **Weekly encrypted backups** (off-machine)
   - Cloud storage or external drive
   - Disaster recovery

3. **Monthly archive** (long-term)
   - Keep for 1 year
   - Major milestones

### Audit Your Data

Periodically review what's stored:
```bash
# Check for sensitive patterns
cheese-brain search "api_key" --format json | jq '.[] | select(.data.api_key)'
cheese-brain search "password" --format json | jq '.[] | select(.data.password)'

# Move sensitive data to password manager
# Then update entities with references instead
```

## 📚 Related Documentation

- [Backup & Recovery](BACKUP_RECOVERY.md) - Automated backups, retention, disaster recovery
- [README](README.md) - Installation, usage, features
- [FTS Documentation](FTS.md) - Full-text search guide

## 🐛 Reporting Security Issues

Found a security vulnerability? Please email (or DM) instead of filing a public GitHub issue.

GitHub: [@mhugo22](https://github.com/mhugo22)
