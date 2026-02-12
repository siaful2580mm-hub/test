'use client';
import { Wallet } from 'lucide-react';

export default function WalletPage() {
  return (
    <div className="p-4">
      <h1 className="text-xl font-bold text-[#0A2540] mb-4">আমার ওয়ালেট</h1>
      
      {/* Balance Box */}
      <div className="bg-gradient-to-r from-[#0A2540] to-[#0057FF] p-6 rounded-2xl text-white shadow-lg mb-6">
        <p className="text-sm opacity-80">বর্তমান ব্যালেন্স</p>
        <h2 className="text-3xl font-bold mt-1">৳ ১৫০.০০</h2>
      </div>

      {/* Withdraw Form */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <h3 className="font-bold mb-4 flex items-center gap-2">
          <Wallet size={20} className="text-[#E2136E]" /> টাকা উত্তোলন
        </h3>
        
        <div className="space-y-3">
          <div>
            <label className="text-xs font-bold text-gray-500">মেথড সিলেক্ট করুন</label>
            <select className="w-full border p-2 rounded bg-gray-50 mt-1">
              <option>bKash</option>
              <option>Nagad</option>
            </select>
          </div>
          
          <div>
            <label className="text-xs font-bold text-gray-500">মোবাইল নাম্বার</label>
            <input type="number" placeholder="017..." className="w-full border p-2 rounded bg-gray-50 mt-1" />
          </div>

          <div>
            <label className="text-xs font-bold text-gray-500">টাকার পরিমাণ</label>
            <input type="number" placeholder="৫০" className="w-full border p-2 rounded bg-gray-50 mt-1" />
          </div>

          <button className="w-full bg-[#E2136E] text-white font-bold py-3 rounded-lg mt-2">
            উত্তোলন করুন
          </button>
        </div>
      </div>
    </div>
  );
        }
