## Prerequisites

- Ensure your **Node.js** version is **16.14.0** or higher. Check your version with:
  ```sh
  node -v
  ```
- If Node.js is not installed, download and install it from the [official website](https://nodejs.org/).

## Environment

**`frontend/.env`** holds all **`VITE_*`** for both **`npm run dev`** and **`docker compose --profile frontend up --build`** (run from **`lungo/`**; the UI container loads only this file — not **`lungo/.env`**).

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
