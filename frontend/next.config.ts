import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    // ⚠️ Permite que el build continúe aunque haya errores de TypeScript
    ignoreBuildErrors: true,
  },
  eslint: {
    // ⚠️ Permite que el build continúe aunque haya errores de ESLint
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
