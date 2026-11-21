# Situation Desk

Responsive situational-awareness dashboard and Node.js API connector service.

## Run locally
Node.js 18+: `npm install && npm start`, then visit http://localhost:5050.

## API routes
- GET /api/health
- GET /api/connectors
- PUT /api/connectors/:id
- POST /api/connectors/:id/sync
- GET /api/unified

The listed providers are starter connector entries, not verified integrations. Obtain each provider's official API documentation, credentials and permission before configuring endpoints. API keys are server-side and configuration data is excluded from Git.

## Deploy
Deploy on Render from this repository. The included render.yaml sets Node runtime, npm start, and /api/health. GitHub Pages is static hosting only and cannot run this backend or securely store API keys.
