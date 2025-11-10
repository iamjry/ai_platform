/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost/api',
  },

  // Image optimization
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
  },

  // API rewrites (for development)
  async rewrites() {
    return [
      {
        source: '/api/agent/:path*',
        destination: 'http://localhost:8002/:path*', // Agent Service
      },
      {
        source: '/api/mcp/:path*',
        destination: 'http://localhost:8001/:path*', // MCP Server
      },
      {
        source: '/api/litellm/:path*',
        destination: 'http://localhost:4000/:path*', // LiteLLM
      },
    ];
  },

  // Production optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Experimental features
  experimental: {
    optimizePackageImports: ['@mui/material', '@mui/icons-material'],
  },

  // Output for Docker
  output: 'standalone',
};

module.exports = nextConfig;
