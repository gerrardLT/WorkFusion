import type { Metadata } from 'next';
import { Inter, Noto_Sans_SC, Noto_Serif_SC } from 'next/font/google';
import './globals.css';
import { cn } from '@/lib/utils';
import { CompanyProvider } from '@/contexts/company-context';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const notoSansSC = Noto_Sans_SC({
  subsets: ['latin'],
  variable: '--font-noto-sans-sc',
  display: 'swap',
  weight: ['300', '400', '500', '600', '700'],
});

const notoSerifSC = Noto_Serif_SC({
  subsets: ['latin'],
  variable: '--font-noto-serif-sc',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: {
    template: '%s | 多场景AI知识问答系统',
    default: '多场景AI知识问答系统',
  },
  description: '基于AI的多场景智能问答平台，支持招投标和企业管理专业问答服务',
  keywords: [
    '招投标',
    '企业管理',
    'AI问答',
    'RAG',
    '智能问答',
    '多场景',
    '人工智能',
    '知识库',
  ],
  authors: [{ name: '多场景AI团队' }],
  creator: '多场景AI团队',
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3005'),
  openGraph: {
    type: 'website',
    locale: 'zh_CN',
    url: '/',
    siteName: '多场景AI知识问答系统',
    title: '多场景AI知识问答系统',
    description: '基于AI的多场景智能问答平台',
    images: [
      {
        url: '/images/og-image.png',
        width: 1200,
        height: 630,
        alt: '多场景AI知识问答系统',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: '多场景AI知识问答系统',
    description: '基于AI的多场景智能问答平台',
    images: ['/images/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/manifest.json',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html
      lang="zh-CN"
      suppressHydrationWarning
      className={cn(
        inter.variable,
        notoSansSC.variable,
        notoSerifSC.variable
      )}
    >
      <head>
        {/* Preconnect to external domains for performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />

        {/* Security headers */}
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-Frame-Options" content="DENY" />
        <meta httpEquiv="X-XSS-Protection" content="1; mode=block" />

        {/* Theme color for mobile browsers */}
        <meta name="theme-color" content="#2563eb" />
        <meta name="msapplication-TileColor" content="#2563eb" />

        {/* Apple Web App */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="多场景AI" />

        {/* Microsoft */}
        <meta name="msapplication-config" content="/browserconfig.xml" />
      </head>
      <body
        className={cn(
          'min-h-screen bg-background font-sans antialiased',
          'selection:bg-blue-100 selection:text-blue-900',
          'no-yellow'
        )}
      >
        <CompanyProvider>
          <div className="relative flex min-h-screen flex-col">
            <div className="flex-1">
              {children}
            </div>
          </div>
        </CompanyProvider>
      </body>
    </html>
  );
}
