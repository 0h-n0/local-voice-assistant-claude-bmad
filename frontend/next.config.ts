import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable turbopack with empty config to satisfy Next.js 16
  turbopack: {},
  // Webpack config for fallback when using webpack mode
  webpack: (config) => {
    // Handle onnxruntime-web for VAD
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      path: false,
      crypto: false,
    };

    return config;
  },
  // Allow loading WASM files
  async headers() {
    return [
      {
        source: "/:path*.wasm",
        headers: [
          {
            key: "Content-Type",
            value: "application/wasm",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
