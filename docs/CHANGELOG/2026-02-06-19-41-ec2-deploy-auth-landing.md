# EC2 Deployment, Auth & Landing Page

**Date**: 2026-02-06 19:41:00

## Summary

Add role-based JWT authentication, redesigned alpine-themed landing page, frontend auth flow, and EC2 deployment infrastructure with Nginx/SSL.

## Changes

- Added: `UserRole` enum (user/admin) and `role` column on User model
- Added: Role claim in JWT tokens and `get_current_admin_user` guard
- Added: Admin-only `GET /users/` list endpoint
- Added: `api.cli` module for seeding admin users from CLI
- Added: Full landing page redesign with alpine mountain theme, hero section, and feature cards
- Added: Frontend auth system (API client, AuthContext, login/register/dashboard pages, route protection)
- Added: shadcn/ui card, input, label components
- Added: Alpine color theme in globals.css
- Added: Terraform EC2 config (instance, security group, EIP, Route53 DNS, SSH key pair)
- Added: Production Docker Compose with Nginx reverse proxy and Certbot
- Added: Nginx config with HTTPS termination, security headers, and HTTP→HTTPS redirect
- Added: `scripts/setup-production.sh` — single E2E orchestrator (infra → wait → deploy → SSL → admin)
- Added: `scripts/deploy.sh` — self-contained deploy (reads host/key from terraform output)
- Added: `scripts/init-ssl.sh` — remote SSL setup via SSH
- Added: `scripts/backup-db.sh` — remote DB backup to local file
- Added: `.env.production.example` template (auto-generated with secrets by setup script)
- Modified: `Makefile` with `production`, `infra`, `infra-destroy`, `deploy`, `init-ssl`, `backup`, `lint`, `test`, `create-admin` targets
- Modified: `.gitignore` with Terraform, SSL, backup, and .env.production exclusions

## Affected Components

- `backend/vector_db/models/user.py` - UserRole enum and role column
- `backend/api/core/security.py` - Role parameter in JWT creation
- `backend/api/v1/auth.py` - Role in token, admin guard dependency
- `backend/api/v1/users.py` - Role in response, admin list endpoint
- `backend/api/cli.py` - Admin seed CLI
- `frontend/web/src/app/page.tsx` - Full landing page redesign
- `frontend/web/src/app/layout.tsx` - AuthProvider wrapper
- `frontend/web/src/app/globals.css` - Alpine color theme
- `frontend/web/src/lib/api.ts` - API client with JWT handling
- `frontend/web/src/contexts/auth-context.tsx` - Auth context provider
- `frontend/web/src/app/login/page.tsx` - Login page
- `frontend/web/src/app/register/page.tsx` - Registration page
- `frontend/web/src/app/dashboard/page.tsx` - Protected dashboard
- `frontend/web/src/components/auth/protected-route.tsx` - Route guard
- `infrastructure/terraform/environments/dev/` - EC2, DNS, key pair config
- `docker-compose.prod.yml` - Production compose with Nginx
- `nginx/` - Nginx configuration files
- `scripts/` - Deploy, SSL, backup scripts
- `Makefile` - New targets
