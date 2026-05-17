import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: "standalone" removed — using Render native Node.js runtime
  // which runs `next start` directly (reads PORT env var automatically)
};

export default nextConfig;
