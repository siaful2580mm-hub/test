'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      alert("ভুল ইমেইল বা পাসওয়ার্ড!");
    } else {
      router.push('/home');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center p-6 bg-white">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-[#0A2540]">TaskKing</h1>
        <p className="text-gray-500">লগিন করে কাজ শুরু করুন</p>
      </div>

      <form onSubmit={handleLogin} className="space-y-4">
        <input
          type="email"
          placeholder="ইমেইল"
          className="w-full p-3 border rounded-lg bg-gray-50 focus:outline-none focus:border-[#E2136E]"
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="পাসওয়ার্ড"
          className="w-full p-3 border rounded-lg bg-gray-50 focus:outline-none focus:border-[#E2136E]"
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button 
          disabled={loading}
          className="w-full bg-[#E2136E] text-white font-bold py-3 rounded-lg hover:opacity-90"
        >
          {loading ? "অপেক্ষা করুন..." : "লগিন করুন"}
        </button>
      </form>

      <p className="text-center mt-6 text-sm">
        একাউন্ট নেই? <Link href="/register" className="text-[#E2136E] font-bold">রেজিস্টার করুন</Link>
      </p>
    </div>
  );
            }
