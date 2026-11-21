# Situation Desk — Unified Situational Awareness Dashboard

Node.js dashboard and API connector hub for Glint Terminal, SitDeck, WorldwatchUK, WorldMonitor, OSIRIS AI, ShadowBroker, WatchBoard, Monitor the Situation, and Hormuz Crisis Tracker.

## Run locally

Requires Node.js 18+.

```bash
npm install
npm start
```

Open http://localhost:5050.

## API

- GET /api/health — health check
- GET /api/connectors — configured connectors (keys are never returned)
- PUT /api/connectors/:id — configure a connector
- POST /api/connectors/:id/sync — fetch configured GET endpoints
- GET /api/unified — normalized cached reports

Connector credentials are stored server-side in data/config.json, which is excluded from Git. Configure HTTPS API URLs and only provider-authorized endpoints. Official API access, authentication, and terms must be verified for each provider before use.

## Deploy

This repository includes render.yaml. In Render, create a Blueprint from this GitHub repository. Build: npm install. Start: npm start. Health check: /api/health. The server binds to 0.0.0.0 and uses the PORT environment variable.

The dashboard starts with no connected providers and no fabricated live events. Add a provider's authorized base URL and endpoint paths in Platform Integrations, then configure API keys on the server before syncing.
