import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 配置代理转发：让前端请求 /api 时，自动转给后端 8000 端口
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;