# PrivacyStressApp Backend

Express + Prisma API for the NeuroMove research prototype.

## Responsibilities

- Session authentication.
- Encrypted ASD profile storage and recovery.
- Derived-metric check-in persistence.
- Contextual stress prediction baseline.
- Admin/research analytics.
- MEC node and federated update metadata.

## Run

```powershell
pnpm install
bunx prisma generate
bunx prisma db push
bun src/index.ts
```

The default `.env` points Prisma to `prisma/dev.db`.

## Demo Accounts

Seeded automatically when `SEED_DEMO_DATA=true`:

- `demo@neuromove.app / demo12345`
- `research@neuromove.app / research123`
- `admin@neuromove.app / admin12345`

## Privacy Boundary

The protected ASD profile vector is transformed and encrypted before storage. Check-ins store only derived metrics, stress prediction output, and support flags. The raw submitted contextual payload is used for inference and then discarded by the persistence layer.
