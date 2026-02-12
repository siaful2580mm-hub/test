'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({ name: '', mobile: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);

    // 1. Sign up user
    const { data, error } = await supabase.auth.signUp({
      email: formData.email,
      password: formData.password,
      options: {
        data: {
          full_name: formData.name,
          mobile_number: formData.mobile,
        }
      }
    });

    if (error) {
      alert("রেজিস্ট্রেশন ব্যর্থ হয়েছে: " + error.message);
    } else {
      alert("রেজিস্ট্রেশন সফল! এখন লগিন করুন।");
      router.push('/login');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center p-6 bg-white">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-[#0A2540]">নতুন একাউন্ট খুলুন</h1>
      </div>

      <form onSubmit={handleRegister} className="space-y-4">
        <input
          type="text"
          placeholder="আপনার নাম"
          className="w-full p-3 border rounded-lg bg-gray-50"
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          required
        />
        <input
          type="text"
          placeholder="মোবাইল নাম্বার"
          className="w-full p-3 border rounded-lg bg-gray-50"
          onChange={(e) => setFormData({...formData, mobile: e.target.value})}
          required
        />
        <input
          type="email"
          placeholder="ইমেইল"
          className="w-full p-3 border rounded-lg bg-gray-50"
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          required
        />
        <input
          type="password"
          placeholder="পাসওয়ার্ড (কমপক্ষে ৬ সংখ্যা)"
          className="w-full p-3 border rounded-lg bg-gray-50"
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
        />
        <button 
          disabled={loading}
          className="w-full bg-[#0A2540] text-white font-bold py-3 rounded-lg hover:opacity-90"
        >
          {loading ? "খোলা হচ্ছে..." : "রেজিস্টার করুন"}
        </button>
      </form>

      <p className="text-center mt-6 text-sm">
        অলরেডি একাউন্ট আছে? <Link href="/login" className="text-[#E2136E] font-bold">লগিন</Link>
      </p>
    </div>
  );
            }
