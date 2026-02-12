'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';

export default function BalanceCard({ balance }) {
  const [showBalance, setShowBalance] = useState(false);

  const handleTap = () => {
    setShowBalance(true);
    setTimeout(() => setShowBalance(false), 3000);
  };

  return (
    <div className="flex justify-center -mt-6 mb-6 relative z-10">
      <div 
        onClick={handleTap}
        className="bg-white text-[#E2136E] px-4 py-2 rounded-full shadow-lg border border-gray-100 cursor-pointer flex items-center gap-2 transition-all active:scale-95"
      >
        <span className="font-bold">৳</span>
        {showBalance ? (
          <motion.span 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="font-bold"
          >
            {balance || "0.00"}
          </motion.span>
        ) : (
          <span className="text-sm font-medium">ব্যালেন্স দেখুন</span>
        )}
      </div>
    </div>
  );
}
