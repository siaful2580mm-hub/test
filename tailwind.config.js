/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#0A2540",   // Trust Navy
          blue: "#0057FF",   // Secure Blue
          pink: "#E2136E",   // bKash Pink
          light: "#F3F4F6",  // Background
        }
      },
      fontFamily: {
        sans: ['Inter', 'SolaimanLipi', 'sans-serif'], // বাংলার জন্য ফন্ট
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
};
