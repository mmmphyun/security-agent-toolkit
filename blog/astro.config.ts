import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import { SITE } from "./src/config";

export default defineConfig({
  site: SITE.url,
  base: SITE.basePath,
  trailingSlash: "always",
  markdown: {
    shikiConfig: {
      theme: "github-dark-dimmed",
      wrap: true,
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
