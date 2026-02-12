import { BellRing } from 'lucide-react';

export default function Notice({ text }) {
  return (
    <div className="mx-4 mt-4 bg-white p-1 rounded-full shadow-sm border border-gray-100 flex items-center gap-2 overflow-hidden">
      <div className="bg-[#0A2540] text-white p-2 rounded-full">
        <BellRing size={16} />
      </div>
      <div className="flex-1 overflow-hidden whitespace-nowrap">
        <div className="animate-marquee inline-block text-sm text-gray-600 font-medium">
          {text || "স্বাগতম TaskKing-এ। প্রতিদিন নিয়ম মেনে কাজ করুন এবং পেমেন্ট নিন।"}
        </div>
      </div>
      
      {/* Tailwind Config এ animate-marquee যোগ করতে হবে, অথবা নিচের স্টাইল ব্যবহার করুন */}
      <style jsx>{`
        .animate-marquee {
          display: inline-block;
          padding-left: 100%;
          animation: marquee 15s linear infinite;
        }
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-100%); }
        }
      `}</style>
    </div>
  );
}
