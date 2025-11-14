'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Navbar() {
  const pathname = usePathname();

  const links = [
    {
      href: '/battle',
      label: 'Parse Battle',
      isActive: pathname === '/' || pathname?.startsWith('/battle'),
    },
    {
      href: '/parse',
      label: 'Parse & Compare',
      isActive: pathname?.startsWith('/parse'),
    },
    {
      href: '/datasets',
      label: 'Datasets',
      isActive: pathname?.startsWith('/datasets') || pathname?.startsWith('/results'),
    },
  ];

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo / Brand */}
          <Link href="/battle" className="text-2xl font-bold">
            DocAgent Arena
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6">
            {links.map(({ href, label, isActive }) => (
              <Link
                key={href}
                href={href}
                className={`text-sm font-medium transition-colors hover:text-primary ${
                  isActive ? 'text-primary' : 'text-muted-foreground'
                }`}
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
