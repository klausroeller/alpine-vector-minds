# Remove Terraform state dependency from deploy scripts

**Date**: 2026-02-07 18:30:00

## Summary

All scripts now use the domain name and a conventional SSH key path instead of requiring local Terraform state.

## Changes

- Modified: `scripts/deploy.sh` — use `DEPLOY_HOST` (default: `alpine-vector-minds.de`) and `KEY_PATH` (default: `~/.ssh/avm-ec2-key.pem`)
- Modified: `scripts/backup-db.sh` — same pattern
- Modified: `scripts/init-ssl.sh` — same pattern
- Modified: `scripts/setup-production.sh` — copies SSH key to `~/.ssh/avm-ec2-key.pem` after Terraform creates it
- Modified: `README.md` — updated env vars table and added deployment prerequisites section

## Affected Components

- `scripts/` — all deploy-related scripts
- `README.md` — deployment documentation
