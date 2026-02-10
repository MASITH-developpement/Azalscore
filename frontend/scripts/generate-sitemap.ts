import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const baseUrl = 'https://azalscore.com';
const pages = [
  { url: '/', priority: '1.0', changefreq: 'daily' },
  { url: '/features', priority: '0.9', changefreq: 'weekly' },
  { url: '/pricing', priority: '0.9', changefreq: 'weekly' },
  { url: '/demo', priority: '0.8', changefreq: 'weekly' },
  { url: '/contact', priority: '0.8', changefreq: 'monthly' },
  { url: '/docs', priority: '0.7', changefreq: 'weekly' },
  { url: '/about', priority: '0.6', changefreq: 'monthly' },
];

const today = new Date().toISOString().split('T')[0];

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${pages.map(page => `  <url>
    <loc>${baseUrl}${page.url}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`).join('\n')}
</urlset>`;

const outputPath = path.join(__dirname, '../public/sitemap.xml');
fs.writeFileSync(outputPath, sitemap, 'utf-8');

console.log('✅ Sitemap generated:', outputPath);
