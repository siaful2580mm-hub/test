'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, ListTodo, Wallet, User } from 'lucide-react';

export default function BottomNav() {
  const pathname = usePathname();

  const navItems = [
    { href: '/home', label: 'হোম', icon: Home },
    { href: '/tasks', label: 'টাস্ক', icon: ListTodo },
    { href: '/wallet', label: 'ওয়ালেট', icon: Wallet },
    { href: '/profile', label: 'প্রোফাইল', icon: User },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-6 py-2 flex justify-between items-center z-50 max-w-md mx-auto shadow-[0_-5px_10px_rgba(0,0,0,0.05)]">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link key={item.href} href={item.href} className="flex flex-col items-center gap-1">
            <item.icon 
              size={24} 
              className={`transition-all ${isActive ? 'text-[#E2136E] scale-110' : 'text-gray-400'}`} 
              strokeWidth={isActive ? 2.5 : 2}
            />
            <span className={`text-[10px] font-medium ${isActive ? 'text-[#E2136E]' : 'text-gray-500'}`}>
              {item.label}
            </span>
          </Link>
        );
      })}
    </div>
  );
                }
