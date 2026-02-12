import Link from 'next/link';
import { ArrowRight, ShieldCheck, Zap, Globe } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Hero Section */}
      <div className="bg-[#0A2540] text-white p-8 rounded-b-[40px] shadow-2xl">
        <div className="flex justify-between items-center mb-8">
          <div className="font-bold text-2xl">TaskKing</div>
          <div className="bg-white/10 px-3 py-1 rounded-full text-xs">Beta v1.0</div>
        </div>
        
        <h1 className="text-4xl font-bold leading-tight mb-4">
          ঘরে বসে <br/> <span className="text-[#0057FF]">আয় করুন</span>
        </h1>
        <p className="text-gray-300 mb-8 text-sm">
          বাংলাদেশের সবচেয়ে বিশ্বস্ত মাইক্রো-টাস্কিং প্ল্যাটফর্ম। ছোট ছোট কাজ করুন এবং প্রতিদিন পেমেন্ট নিন।
        </p>

        <div className="flex gap-4">
          <Link href="/login" className="flex-1 bg-[#E2136E] text-center py-3 rounded-xl font-bold shadow-lg hover:opacity-90 transition">
            লগিন করুন
          </Link>
          <Link href="/register" className="flex-1 bg-white text-[#0A2540] text-center py-3 rounded-xl font-bold shadow-lg hover:bg-gray-100 transition">
            রেজিস্টার
          </Link>
        </div>
      </div>

      {/* Features */}
      <div className="p-6 space-y-6 mt-4">
        <FeatureItem 
          icon={<Zap className="text-yellow-500" />} 
          title="দ্রুত পেমেন্ট" 
          desc="বিকাশ ও নগদে পেমেন্ট নিন মাত্র ১০ মিনিটে।" 
        />
        <FeatureItem 
          icon={<ShieldCheck className="text-green-500" />} 
          title="শতভাগ নিরাপদ" 
          desc="আপনার তথ্য এবং ব্যালেন্স সম্পূর্ণ সুরক্ষিত।" 
        />
        <FeatureItem 
          icon={<Globe className="text-blue-500" />} 
          title="সহজ কাজ" 
          desc="ভিডিও দেখা এবং লাইক দেওয়ার মত সহজ কাজ।" 
        />
      </div>

      {/* Footer */}
      <div className="mt-auto p-6 text-center text-xs text-gray-400">
        &copy; 2024 TaskKing Ultimate Edition.
      </div>
    </div>
  );
}

function FeatureItem({ icon, title, desc }) {
  return (
    <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl border border-gray-100">
      <div className="bg-white p-3 rounded-full shadow-sm">{icon}</div>
      <div>
        <h3 className="font-bold text-[#0A2540]">{title}</h3>
        <p className="text-xs text-gray-500 mt-1">{desc}</p>
      </div>
    </div>
  );
    }
