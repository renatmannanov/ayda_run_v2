/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Design tokens from UI spec
                'accent-active': '#f97316',
                'accent-success': '#16a34a',
                'accent-warning': '#d97706',
            },
        },
    },
    plugins: [],
}
