# Production Secrets Configuration

This directory contains sensitive configuration files for production deployment.

## Required Secret Files

Create the following files in this directory before deploying:

### 1. `postgres_password.txt`
PostgreSQL database password
```bash
echo "your_secure_postgres_password_here" > postgres_password.txt
```

### 2. `redis_password.txt`
Redis cache password
```bash
echo "your_secure_redis_password_here" > redis_password.txt
```

### 3. `jwt_secret.txt`
JWT signing secret (use a strong random string)
```bash
openssl rand -base64 32 > jwt_secret.txt
```

### 4. `smtp_password.txt`
SMTP server password for email notifications
```bash
echo "your_smtp_password_here" > smtp_password.txt
```

## Security Guidelines

1. **Never commit these files to version control**
2. **Use strong, unique passwords for each service**
3. **Rotate secrets regularly**
4. **Ensure proper file permissions** (600 for files, 700 for directory)

## Setting Permissions

```bash
chmod 700 secrets/
chmod 600 secrets/*.txt
```

## Generating Secure Passwords

```bash
# Generate random passwords
openssl rand -base64 32
# or
pwgen -s 32 1
```

## Environment-Specific Secrets

For different environments, you may want to use different secret directories:

```bash
secrets/
├── production/
│   ├── postgres_password.txt
│   ├── redis_password.txt
│   ├── jwt_secret.txt
│   └── smtp_password.txt
├── staging/
│   ├── postgres_password.txt
│   ├── redis_password.txt
│   ├── jwt_secret.txt
│   └── smtp_password.txt
└── README.md
```

## Backup Considerations

- Ensure secrets are included in your secure backup strategy
- Never store secrets in plain text backups
- Consider using encrypted backup solutions for secrets