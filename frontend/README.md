# Cloud9 ERP - Frontend

React + TypeScript frontend for Cloud9 ERP inventory management system.

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

Starts the Vite dev server at `http://localhost:5173`. API requests proxy to `http://localhost:8000`.

## Production Build

```bash
npm run build
```

Output goes to `dist/`. Serve with any static file server or Nginx.

## API Integration

The frontend connects to the backend API at `http://localhost:8000` by default. Configure via environment:

```bash
# .env
VITE_API_URL=http://localhost:8000
```

### Authentication

All authenticated API requests include an `Authorization: Bearer <token>` header automatically via the axios client in `src/api/client.ts`. Tokens are stored in `localStorage` as `access_token` and `refresh_token`.

## Project Structure

```
src/
  api/        # API client and endpoint modules
  components/ # Reusable UI components
  context/    # React context providers (auth)
  hooks/      # React hooks (react-query wrappers)
  layouts/    # Page layout components
  pages/      # Route page components
  router/     # Route definitions
  types/      # TypeScript type definitions
  utils/      # Utility functions and validation schemas
```

## Tech Stack

- React 19
- TypeScript
- Vite
- Tailwind CSS
- React Router v7
- TanStack React Query v5
- React Hook Form + Zod
- Axios
- Lucide React (icons)
- react-hot-toast
