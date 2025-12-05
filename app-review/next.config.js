/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
    unoptimized: false, // Enable Next.js image optimization
  },
  // Exclude public/apps from serverless function bundle
  // These files are served as static assets and don't need to be bundled
  // Per Vercel guide: Use outputFileTracingExcludes in next.config.js (not vercel.json)
  outputFileTracingExcludes: {
    '*': [
      '**/public/apps/**',
    ],
  },
  experimental: {
    // Other experimental features if needed
  },
};

module.exports = nextConfig;
