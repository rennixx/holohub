/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Allow production builds to complete even with lint errors
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Allow production builds to complete even with type errors
    ignoreBuildErrors: true,
  },

  // Image domains for S3/MinIO
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '9000',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
      },
    ],
  },

  // Webpack configuration for Three.js
  webpack: (config) => {
    config.externals.push({
      'utf-8-validate': 'commonjs utf-8-validate',
      'bufferutil': 'commonjs bufferutil',
    });

    // Optimize chunk splitting to prevent vendor chunk issues
    config.optimization = {
      ...config.optimization,
      splitChunks: {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...config.optimization.splitChunks?.cacheGroups,
          tanstack: {
            name: 'tanstack',
            test: /[\\/]node_modules[\\/](@tanstack|@tanstack\/react-query)/,
            priority: 30,
            reuseExistingChunk: true,
          },
        },
      },
    };

    return config;
  },

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_S3_ENDPOINT: process.env.NEXT_PUBLIC_S3_ENDPOINT || 'http://localhost:9000',
    NEXT_PUBLIC_S3_BUCKET: process.env.NEXT_PUBLIC_S3_BUCKET || 'holohub-dev',
  },
};

export default nextConfig;
