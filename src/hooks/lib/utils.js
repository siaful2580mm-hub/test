import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Tailwind Class Merger
 * একাধিক ক্লাস কন্ডিশনালি যোগ করতে এটি ব্যবহার করা হয়।
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
