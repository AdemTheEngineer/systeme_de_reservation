export const environment = {
  production: false,
  // Backend is a Django monolith (all bounded contexts under one process),
  // not the three separate microservices assumed in the original brief —
  // see project memory `project-backend-contract` for details.
  // Relative path: the Django backend has no CORS headers configured (and we
  // must not edit backend files), so `ng serve`'s dev-server proxy
  // (proxy.conf.json) forwards this same-origin path to localhost:8000.
  apiBaseUrl: '/api/v2',
};
