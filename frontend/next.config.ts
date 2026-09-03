import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // In production / Docker Compose, default to container hostname http://reach_backend:8000.
    // In local dev outside Docker (npm run dev on Mac), default to http://localhost:8000.
    const rawBackendUrl =
      process.env.BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      (process.env.NODE_ENV === "production" ? "http://reach_backend:8000" : "http://localhost:8000");

    const backendUrl = rawBackendUrl.replace(/\/+$/, "");

    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
