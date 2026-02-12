export default function Header({ user }) {
  return (
    <div className="bg-[#E2136E] pt-8 pb-12 px-6 rounded-b-[30px] shadow-md relative">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-[#E2136E] font-bold text-xl border-2 border-white/50">
          {user?.full_name?.charAt(0) || "U"}
        </div>
        <div className="text-white">
          <p className="text-xs opacity-90">স্বাগতম,</p>
          <h2 className="text-xl font-bold">{user?.full_name || "Guest"}</h2>
        </div>
      </div>
    </div>
  );
}
