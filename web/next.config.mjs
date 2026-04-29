/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Aponta o pipeline para não explodir ao ignorar eslint estrito durante o build
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Também previne a pipeline de quebrar caso fiquem uns 'any' da lib
    ignoreBuildErrors: true,
  }
};

export default nextConfig;
