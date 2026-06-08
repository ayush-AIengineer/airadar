import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Pin file tracing to this app (multiple lockfiles exist on this machine).
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
