export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#B1AFFF", // Lavender
        secondary: "#FFDAB9", // Peach
        accent: "#ADD8E6", // Light Blue
        dark: "#2A2A35", 
        light: "#FAFAFA",
        surface: "#F3F4F6", 
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      }
    },
  },
  plugins: [],
}
