import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for Docker deployment — emits .next/standalone/server.js
  output: "standalone",
};

export default nextConfig;
