/**
 * Layout with auth guard and sidebar
 */
import './globals.css';
import { Providers } from '@/lib/providers';
import { Sidebar } from '@/components/layout/sidebar';

export const metadata = {
  title: 'Com Management',
  description: 'Communication Management Backend System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>
          <div className="flex h-screen overflow-hidden bg-gray-50">
            <Sidebar />
            <main className="flex-1 overflow-auto">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
