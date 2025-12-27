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
  // Allow loading WASM files and enable SharedArrayBuffer
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
      {
        source: "/:path*",
        headers: [
          {
            key: "Cross-Origin-Opener-Policy",
            value: "same-origin",
          },
          {
            key: "Cross-Origin-Embedder-Policy",
            value: "require-corp",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
