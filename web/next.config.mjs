/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // tsc --noEmit is run separately in CI; skip the redundant check during next build
    ignoreBuildErrors: true,
  },
  async rewrites() {
    if (process.env.NODE_ENV !== 'development') return [];
    const target = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    return [{ source: '/api/:path*', destination: `${target}/api/:path*` }];
  },
};
export default nextConfig;
