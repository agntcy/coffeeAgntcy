## Prerequisites

- **Node.js** 24.x with **npm** 11.10.1 or higher. Check your versions with:
  ```sh
  node -v
  npm -v
  ```
- If Node.js is not installed, download and install it from the [official website](https://nodejs.org/).

## Environment

**`frontend/.env`** holds all **`VITE_*`** for both **`npm run dev`** and the **`ui`** Docker service (run Compose from **`lungo/`**; the UI container loads only this file — not **`lungo/.env`**).

**Working with Docker backends:** If you use **`npm run dev`**, remove **`frontend`** from **`COMPOSE_PROFILES`** in **`lungo/.env`** and run **`docker compose up --build`** from **`lungo/`** so the **`ui`** container does not compete for port **3000**. If the UI should run only in Docker, keep **`frontend`** in **`COMPOSE_PROFILES`** and use **`docker compose up --build`** alone (see the Lungo README).

Create it once:

```sh
cp .env.example .env
```

## Quick Start

1. Install the necessary dependencies:

   ```sh
   npm install
   ```

2. Start the development server:

   ```sh
   npm run dev
   ```
