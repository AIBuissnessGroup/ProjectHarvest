import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: "class",
    content: ["./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                brand: {
                    50: "#e6f7fd",
                    100: "#cceffa",
                    200: "#99dff6",
                    300: "#66cff1",
                    400: "#33bfed",
                    500: "#14b1e5",
                    600: "#108dba",
                    700: "#0c6a8c",
                    800: "#08475d",
                    900: "#04232f",
                    950: "#021119",
                },
            },
            borderRadius: { xl: "1rem", "2xl": "1.25rem" },
            boxShadow: { soft: "0 6px 20px rgba(0,0,0,0.08)" },
        },
    },
    plugins: [require("tailwindcss-animate")],
};

export default config;
