import type { NextConfig } from "next";

// Inside Docker Compose, BACKEND_URL is set (e.g. http://reach_backend:8000).
// Locally on Mac (outside Docker), fallback to http://localhost:8000.
const rawBackendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const backendUrl = rawBackendUrl.replace(/\/+$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
