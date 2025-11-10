/**
 * Root Layout for Next.js App Router
 * Provides theme, font, and basic HTML structure
 */

import type { Metadata } from 'next';
import { Roboto, Noto_Sans_TC } from 'next/font/google';
import { ThemeRegistry } from '@/lib/theme';
import { Providers } from './providers';
import './globals.css';

/**
 * Configure fonts
 */
const roboto = Roboto({
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-roboto',
});

const notoSansTC = Noto_Sans_TC({
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-noto-sans-tc',
});

/**
 * Metadata for the application
 */
export const metadata: Metadata = {
  title: 'AI Platform',
  description: 'AI-powered platform with multi-model support',
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#6750A4', // M3 primary color
};

/**
 * Root Layout Component
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-TW" className={`${roboto.variable} ${notoSansTC.variable}`}>
      <body>
        <ThemeRegistry>
          <Providers>{children}</Providers>
        </ThemeRegistry>
      </body>
    </html>
  );
}
