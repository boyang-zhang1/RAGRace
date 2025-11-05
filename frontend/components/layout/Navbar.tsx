'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Navbar() {
  const pathname = usePathname();

  const links = [
    {
      href: '/datasets',
      label: 'Datasets',
      isActive: pathname === '/' || pathname?.startsWith('/datasets'),
    },
    {
      href: '/results',
      label: 'Results',
      isActive: pathname?.startsWith('/results'),
    },
    {
      href: '/parse',
      label: 'Parse & Compare',
      isActive: pathname?.startsWith('/parse'),
    },
    {
      href: '/dashboard',
      label: 'Run Benchmark',
      isActive: pathname?.startsWith('/dashboard'),
    },
  ];

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo / Brand */}
          <Link href="/datasets" className="text-2xl font-bold">
            RAGRace
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
