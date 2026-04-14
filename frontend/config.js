// ── API Configuration ──────────────────────────────────────────────────────
// This file is the ONLY place you need to change the backend URL.
// For local development:   const BACKEND_URL = 'http://localhost:8000';
// After deploying backend: const BACKEND_URL = 'https://your-app.onrender.com';
//
// On Render static site, set environment variable:
//   BACKEND_URL = https://your-backend.onrender.com
// Then run the build command which replaces this value automatically.

const BACKEND_URL = window.__BACKEND_URL__ || 'http://localhost:8000';
