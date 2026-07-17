/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { unoptimized: true },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://3.107.210.17:9000/:path*',
      },
    ]
  },
}

module.exports = nextConfig
