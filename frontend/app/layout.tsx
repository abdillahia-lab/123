import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from './providers';
import { Sidebar } from '@/components/Sidebar';
import { Copilot } from '@/components/Copilot';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'TerraJinki - The Spirit of Earth Energy',
  description: 'AI-powered renewable energy site intelligence platform',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <Providers>
          <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
            {/* Sidebar */}
            <Sidebar />

            {/* Main content */}
            <main className="flex-1 overflow-hidden">
              {children}
            </main>

            {/* AI Copilot */}
            <Copilot />
          </div>
        </Providers>
      </body>
    </html>
  );
}
