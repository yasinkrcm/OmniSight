"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/odev1", label: "Ödev 1 — PPE" },
  { href: "/odev2", label: "Ödev 2 — Car Damage" },
  { href: "/peoplecounter", label: "People Counter" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="navbar-glass fixed top-0 left-0 right-0 z-50 px-6 py-3 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6c63ff] to-[#00d2ff] flex items-center justify-center">
          <span className="text-white font-bold text-sm">ML</span>
        </div>
        <span className="font-bold text-lg gradient-text hidden md:block">Makine Öğrenmesi Projesi</span>
        <span className="font-bold text-base gradient-text md:hidden">ML Projesi</span>
      </Link>

      <div className="hidden md:flex items-center gap-1">
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                ? "bg-[#6c63ff]/20 text-[#6c63ff]"
                : "text-[#a0a0b5] hover:text-white hover:bg-white/5"
                }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>

      {/* Mobile menu */}
      <div className="md:hidden flex items-center gap-2">
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`px-2 py-1 rounded text-xs font-medium transition-all ${isActive
                ? "bg-[#6c63ff]/20 text-[#6c63ff]"
                : "text-[#a0a0b5]"
                }`}
            >
              {link.label.split("—")[0].trim()}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
