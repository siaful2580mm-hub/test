/** @type {import('next').NextConfig} */
const nextConfig = {
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination:
          process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:5328/api/:path*' // Flask Local Port
            : '/api/:path*',
      },
    ];
  },
  images: {
    domains: ['lh3.googleusercontent.com'], // Google Login ইমেজের জন্য
  },
};

export default nextConfig;
