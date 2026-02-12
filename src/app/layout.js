import "./globals.css";

export const metadata = {
  title: "TaskKing Ultimate",
  description: "Earn Money Online",
};

export default function RootLayout({ children }) {
  return (
    <html lang="bn">
      <body className="bg-gray-50 min-h-screen">
        <main className="max-w-md mx-auto bg-white min-h-screen shadow-2xl">
          {children}
        </main>
      </body>
    </html>
  );
}
