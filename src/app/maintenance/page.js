import { AlertTriangle } from 'lucide-react';

export default function MaintenancePage() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6 text-center">
      <div className="bg-white p-8 rounded-2xl shadow-xl flex flex-col items-center">
        <AlertTriangle size={64} className="text-yellow-500 mb-4" />
        <h1 className="text-2xl font-bold text-[#0A2540]">সার্ভার মেইনটেনেন্স</h1>
        <p className="text-gray-500 mt-2">
          আমাদের সার্ভারের উন্নয়নের কাজ চলছে। দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।
        </p>
        <button 
          onClick={() => window.location.href = '/'}
          className="mt-6 px-6 py-2 bg-[#0A2540] text-white rounded-full text-sm"
        >
          রিফ্রেশ করুন
        </button>
      </div>
    </div>
  );
}
