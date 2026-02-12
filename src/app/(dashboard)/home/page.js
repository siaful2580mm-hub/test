'use client';
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { useSystem } from '@/hooks/useSystem';


// Components
import Header from '@/components/shared/Header';
import BalanceCard from '@/components/dashboard/BalanceCard';
import MenuGrid from '@/components/dashboard/MenuGrid';
import Notice from '@/components/dashboard/Notice';

export default function HomePage() {
  useSystem(); // System check hook
  const [user, setUser] = useState(null);
  const [balance, setBalance] = useState("0.00");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      // 1. User Info
      const { data: { user: authUser } } = await supabase.auth.getUser();
      if (authUser) {
        const { data: profile } = await supabase.from('profiles').select('*').eq('id', authUser.id).single();
        if (profile) {
          setUser(profile);
          setBalance(profile.balance);
        }
      }
      
      // 2. System Notice
      const { data: settings } = await supabase.from('system_settings').select('notice_text').single();
      if (settings) setNotice(settings.notice_text);
    };

    fetchData();
  }, []);

  return (
    <div className="bg-gray-50 min-h-screen pb-24">
      <Header user={user} />
      <BalanceCard balance={balance} />
      <Notice text={notice} />
      <div className="mt-6">
        <MenuGrid />
      </div>
    </div>
  );
}
