import { createClient } from '@supabase/supabase-js';

// Environment Variables থেকে URL এবং Key নেওয়া হচ্ছে
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// ক্লায়েন্ট তৈরি
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
