import BottomNav from '@/components/shared/BottomNav';

export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {children}
      <BottomNav />
    </div>
  );
}
