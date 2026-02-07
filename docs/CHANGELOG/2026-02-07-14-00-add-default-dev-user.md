# Add Default Dev User Seeded on Table Creation

**Date**: 2026-02-07 14:00:00

## Summary

Seed a default admin user automatically when the database is first initialized, removing the need for manual `make create-admin` during dev setup.

## Changes

- Added: `DEFAULT_USER_EMAIL`, `DEFAULT_USER_PASSWORD`, `DEFAULT_USER_NAME` settings in config
- Modified: FastAPI lifespan seeds a default user when the users table is empty and env vars are set
- Modified: `docker-compose.yml` passes new env vars to api service
- Modified: `.env.example` includes dev defaults for the new variables
- Modified: `README.md` documents new environment variables

## Affected Components

- `backend/api/core/config.py` - New optional settings for default user credentials
- `backend/api/main.py` - Seed logic in lifespan after table creation
- `docker-compose.yml` - Pass default user env vars to api service
- `.env.example` - Dev defaults for default user
- `README.md` - Environment variables table updated
