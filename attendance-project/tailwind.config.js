/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'caribbean-current': 'hsla(184, 40%, 33%, 1)',
                'turquoise': 'hsla(169, 89%, 45%, 1)',
                'keppel': 'hsla(169, 55%, 52%, 1)',
                'prussian-blue': 'hsla(204, 62%, 17%, 1)',
            },
            fontFamily: {
                sans: ['Roboto', 'Helvetica', 'Arial', 'sans-serif'],
            },
            animation: {
                fadeIn: "fadeIn 0.3s ease-in-out",
            },
            keyframes: {
                fadeIn: {
                    "0%": { opacity: 0, transform: "scale(0.95)" },
                    "100%": { opacity: 1, transform: "scale(1)" },
                },
            },
        },
    },
    plugins: [],
};
