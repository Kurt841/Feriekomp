import nextConfig from "eslint-config-next";

const config = [
  ...nextConfig,
  {
    ignores: ["**/.next/**", "**/dist/**"],
    rules: {
      "import/no-anonymous-default-export": "off",
      "react-hooks/incompatible-library": "off",
    },
  },
];

export default config;
