'use client';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { LogOut, User, Phone, Share2 } from 'lucide-react';

export default function ProfilePage() {
  const router = useRouter();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
  };

  return (
    <div className="p-4">
      <div className="text-center mb-6 mt-4">
        <div className="w-20 h-20 bg-gray-200 rounded-full mx-auto flex items-center justify-center text-3xl font-bold text-gray-500">
          U
        </div>
        <h2 className="text-xl font-bold mt-2">User Name</h2>
        <p className="text-sm text-gray-500">user@example.com</p>
      </div>

      <div className="space-y-2">
        <ProfileItem icon={User} label="এডিট প্রোফাইল" />
        <ProfileItem icon={Phone} label="সাপোর্ট গ্রুপ" />
        <ProfileItem icon={Share2} label="রেফার করুন" />
        
        <button 
          onClick={handleLogout}
          className="w-full flex items-center gap-3 p-4 bg-red-50 text-red-600 rounded-xl mt-4 font-bold"
        >
          <LogOut size={20} /> লগ আউট
        </button>
      </div>
    </div>
  );
}

function ProfileItem({ icon: Icon, label }) {
  return (
    <div className="flex items-center gap-3 p-4 bg-white rounded-xl shadow-sm border border-gray-100">
      <Icon size={20} className="text-[#0A2540]" />
      <span className="font-medium text-gray-700">{label}</span>
    </div>
  );
            }
