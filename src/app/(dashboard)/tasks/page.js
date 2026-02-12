import { PlayCircle } from 'lucide-react';

export default function TaskPage() {
  const tasks = [
    { id: 1, title: 'ভিডিও দেখুন ১', reward: '৫.০০', color: 'bg-red-100 text-red-600' },
    { id: 2, title: 'ফেসবুক লাইক', reward: '২.০০', color: 'bg-blue-100 text-blue-600' },
    { id: 3, title: 'চ্যানেল সাবস্ক্রাইব', reward: '৩.০০', color: 'bg-red-100 text-red-600' },
    { id: 4, title: 'অ্যাপ রিভিউ', reward: '১০.০০', color: 'bg-green-100 text-green-600' },
  ];

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold text-[#0A2540] mb-4">আজকের টাস্ক</h1>
      <div className="space-y-3">
        {tasks.map((task) => (
          <div key={task.id} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-full ${task.color}`}>
                <PlayCircle size={24} />
              </div>
              <div>
                <h3 className="font-bold text-gray-800">{task.title}</h3>
                <p className="text-xs text-gray-500"> রিওয়ার্ড: ৳{task.reward}</p>
              </div>
            </div>
            <button className="bg-[#0A2540] text-white px-4 py-2 rounded-full text-xs font-bold">
              শুরু করুন
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
