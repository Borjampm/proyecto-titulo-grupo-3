# Frontend

This is the Next.js frontend for the project, generated with `create-next-app` using the App Router, TypeScript, Tailwind CSS, and Turbopack. Follow the guide below to set up the development environment and run the application locally.

## Prerequisites

- Node.js 18.18.0 or newer (Next.js 15 also supports the latest 20.x and 22.x releases)
- npm 9 or newer (bundled with recent Node.js installers)

Confirm your installed versions with:

```bash
node --version
npm --version
```

If you manage multiple Node.js versions, consider using [nvm](https://github.com/nvm-sh/nvm).

## Getting Started

Install dependencies the first time you work on the project (or whenever `package.json` changes):

```bash
npm install
```

Create a `.env.local` file for secrets or environment-specific configuration. Variables defined there override `.env` files and are ignored by Git by default. For example:

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
```

Launch the development server with Turbopack enabled:

```bash
npm run dev
```

The app is served at [http://localhost:3000](http://localhost:3000). Hot reloading refreshes the UI as soon as you save changes.

## Available Scripts

- `npm run dev` — Start the development server using Next.js + Turbopack.
- `npm run build` — Produce an optimized production build (Turbopack under the hood).
- `npm run start` — Serve the production build locally (run after `npm run build`).
- `npm run lint` — Run ESLint against the project source.

## Project Structure

```
frontend/
├─ public/            # Static assets served as-is
├─ src/
│  └─ app/            # App Router entry point, layouts, and routes
│     ├─ globals.css  # Tailwind CSS layer definitions
│     ├─ layout.tsx   # Root layout shared by every route
│     └─ page.tsx     # Home page component
├─ next.config.ts     # Next.js configuration
├─ postcss.config.mjs # PostCSS + Tailwind pipeline
├─ eslint.config.mjs  # ESLint configuration
└─ tsconfig.json      # TypeScript configuration
```

## Tailwind CSS

Tailwind CSS v4 is already wired up. Utilities are available globally via `src/app/globals.css`. You can extend the design system by creating a `tailwind.config.ts` file if custom tokens or plugins are required. Refer to the [Tailwind CSS documentation](https://tailwindcss.com/docs) for usage details.

## Linting & Formatting

ESLint runs with the official `eslint-config-next` ruleset plus TypeScript support. Execute it manually with `npm run lint`. Enable an editor integration (such as the official ESLint extension for VS Code) for inline feedback while coding.

## Building & Deployment

1. Ensure linting passes: `npm run lint`
2. Create a production build: `npm run build`
3. Smoke test the build locally: `npm run start`
4. Deploy following your hosting platform's workflow (e.g., Vercel, container image, or custom Node.js server). Vercel will run `npm run build` automatically when connected to this repository.

## Additional Tips

- Use `src/app/page.tsx` as the entry point for the homepage, or add new routes by creating folders under `src/app/` (each folder needs a `page.tsx`).
- Place reusable UI in a directory such as `src/components/` to keep the App Router tree tidy.
- Keep sensitive configuration out of source control by relying on `.env.local` and your deployment platform's secret management.

You're ready to start building!
