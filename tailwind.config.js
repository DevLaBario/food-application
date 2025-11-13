module.exports = {
  content: [
    "./food_application/templates/**/*.html",
    "./food_application/**/*.py",
    "./users/templates/**/*.html",
    "./users/**/*.py",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
