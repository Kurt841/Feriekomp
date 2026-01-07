import type { NextConfig } from "next";
import path from "path";

// API-konfigurasjon
// Produksjon: Sett API_HOST til backend-service navn (f.eks. "backend" i Docker) eller backend-domene
// Produksjon: Sett NEXT_PUBLIC_API_BASE_URL til din offentlige backend-URL i .env
const apiHost = process.env.API_HOST || 'localhost';
const apiPort = process.env.API_PORT || '5000';
const apiTarget = `http://${apiHost}:${apiPort}`;

const nextConfig: NextConfig = {
  productionBrowserSourceMaps: false,
  outputFileTracingRoot: path.join(__dirname, ".."),

  output: 'standalone',

  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_ENABLE_AI_EXPLANATION: process.env.NEXT_PUBLIC_ENABLE_AI_EXPLANATION,
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiTarget}/:path*`,
      },
    ];
  },
};

export default nextConfig;
