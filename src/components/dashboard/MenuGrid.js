import Link from 'next/link';
import { CheckCircle, Users, Wallet, Headphones } from 'lucide-react';

export default function MenuGrid() {
  const items = [
    { label: "টাস্ক", icon: CheckCircle, color: "text-blue-600", bg: "bg-blue-50", link: "/tasks" },
    { label: "রেফার", icon: Users, color: "text-green-600", bg: "bg-green-50", link: "/profile" }, // Profile এ রেফার লিংক থাকবে
    { label: "উত্তোলন", icon: Wallet, color: "text-[#E2136E]", bg: "bg-pink-50", link: "/wallet" },
    { label: "সাপোর্ট", icon: Headphones, color: "text-orange-600", bg: "bg-orange-50", link: "/profile" },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 px-4">
      {items.map((item, idx) => (
        <Link 
          href={item.link} 
          key={idx}
          className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center gap-2 transition active:scale-95"
        >
          <div className={`p-3 rounded-full ${item.bg} ${item.color}`}>
            <item.icon size={28} />
          </div>
          <span className="font-bold text-gray-700 text-sm">{item.label}</span>
        </Link>
      ))}
    </div>
  );
}
