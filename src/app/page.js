import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 text-center font-sans">
      
      {/* লোগো বা আইকন */}
      <div className="bg-blue-50 p-4 rounded-full mb-6">
        <h1 className="text-4xl font-bold text-[#0A2540]">👑</h1>
      </div>

      {/* হিরো সেকশন */}
      <h1 className="text-3xl font-bold text-[#0A2540] mb-2">
        TaskKing <span className="text-[#0057FF]">Ultimate</span>
      </h1>
      
      <p className="text-gray-500 mb-8 max-w-xs mx-auto">
        বাংলাদেশের সেরা মাইক্রো-টাস্কিং প্ল্যাটফর্ম। ছোট কাজ করুন, বিকাশে পেমেন্ট নিন।
      </p>

      {/* বাটন সেকশন */}
      <div className="w-full max-w-xs space-y-4">
        <Link 
          href="/login" 
          className="block w-full bg-[#E2136E] text-white py-3 rounded-xl font-bold shadow-lg hover:opacity-90 transition"
        >
          লগিন করুন
        </Link>
        
        <Link 
          href="/register" 
          className="block w-full bg-white border-2 border-[#0A2540] text-[#0A2540] py-3 rounded-xl font-bold hover:bg-gray-50 transition"
        >
          নতুন একাউন্ট খুলুন
        </Link>
      </div>

      {/* ফুটার */}
      <div className="mt-12 text-xs text-gray-400">
        &copy; 2026 TaskKing Project.
        <br />
        Status: <span className="text-green-500 font-bold">System Online</span>
      </div>

    </div>
  );
}
