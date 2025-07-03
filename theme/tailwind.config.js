module.exports = {
  content: [
    '../templates/**/*.html',
    './src/**/*.{js,css}',
  ],
  theme: {
    extend: {
      colors: {
        ozon: {
          DEFAULT: '#005BFF',
          dark: '#0041C4',
          light: '#F6F6F6',
        },
      },
      fontFamily: {
        sans: ['"Nunito Sans"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
