import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    // Skip ESLint during production builds (still runs via npm run lint)
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
