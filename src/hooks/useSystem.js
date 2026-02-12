'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { supabase } from '@/lib/supabase';

export function useSystem() {
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const checkSystemStatus = async () => {
      try {
        // ১. ইউজারের সেশন টোকেন নেওয়া (সিকিউর API কলের জন্য)
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;

        // ২. আমাদের Flask Backend (Python) কল করা
        // headers-এ টোকেন পাঠানো হচ্ছে যাতে ব্যাকএন্ড ইউজার চিনতে পারে
        const res = await fetch('/api/system-status', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        
        // ৩. রেসপন্স হ্যান্ডেল করা
        if (res.status === 503) {
          // যদি সার্ভার মেইনটেনেন্সে থাকে (503 Service Unavailable)
          const data = await res.json();
          if (pathname !== '/maintenance') {
            router.push('/maintenance'); // মেইনটেনেন্স পেজে পাঠাও
          }
        } else if (res.ok) {
          const data = await res.json();
          
          // ৪. অ্যাক্টিভেশন চেক লজিক
          // যদি API বলে "activation_required" এবং ইউজার বর্তমানে অ্যাক্টিভেট পেজে নেই
          if (data.action === 'activation_required' && !pathname.startsWith('/activate')) {
             // এবং ইউজার যদি অথেন্টিকেটেড পেজে (যেমন home) থাকে
             if (!pathname.startsWith('/login') && !pathname.startsWith('/register')) {
                router.push('/activate'); // পেমেন্ট পেজে পাঠাও
             }
          }
        }
      } catch (error) {
        console.error("System Check Error:", error);
      } finally {
        setLoading(false);
      }
    };

    // পেজ লোড হলেই চেক করবে
    checkSystemStatus();

  }, [pathname, router]);

  return { loading };
}
