/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        'fgdark': '#161616',
        'bgdark': '#000000',
        'trimdark': '#343434',
        'fglight': 'white',
        'trimlight': '#dcdcdc',
        'ghdarkgreen': '#238636',
        'ghlightgreen': '#2ea043'
      }
    },
  },
  plugins: [],
}
