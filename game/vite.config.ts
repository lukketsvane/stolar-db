import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import sirv from 'sirv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BGUW_DIR = path.resolve(__dirname, '..', 'STOLAR', 'bguw');
const GLB_DIR = path.resolve(__dirname, '..', 'STOLAR', 'glb');
const PBR_DIR = path.resolve(__dirname, '..', 'STOLAR', 'pbr_textured');

export default defineConfig({
  envPrefix: ['VITE_', 'NEXT_PUBLIC_'],
  plugins: [
    react(),
    {
      name: 'serve-bguw-glb-pbr',
      configureServer(server) {
        server.middlewares.use('/bguw', sirv(BGUW_DIR, { dev: true, etag: true }));
        server.middlewares.use('/glb', sirv(GLB_DIR, { dev: true, etag: true }));
        server.middlewares.use('/pbr', sirv(PBR_DIR, { dev: true, etag: true }));
      },
      configurePreviewServer(server) {
        server.middlewares.use('/bguw', sirv(BGUW_DIR, { dev: false, etag: true }));
        server.middlewares.use('/glb', sirv(GLB_DIR, { dev: false, etag: true }));
        server.middlewares.use('/pbr', sirv(PBR_DIR, { dev: false, etag: true }));
      },
    },
  ],
  server: { host: '127.0.0.1' },
});
