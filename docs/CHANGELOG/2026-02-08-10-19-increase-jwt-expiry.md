# Increase JWT Token Expiry

**Date**: 2026-02-08 10:19:00

## Summary

Increase JWT access token expiry from 30 minutes to 7 days.

## Changes

- Modified: default `ACCESS_TOKEN_EXPIRE_MINUTES` from 30 to 10080 (7 days)

## Affected Components

- `backend/api/core/config.py` - Updated default token expiry
- `.env.example` - Updated example value
- `.env.production.example` - Updated example value
