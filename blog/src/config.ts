/**
 * Main theme configuration.
 *
 * `url` is the deployment origin. For GitHub Pages project sites, keep the
 * repository name in `basePath` (for example `/my-blog`). Use `/` for custom
 * domains and `<username>.github.io` repositories.
 */
export const SITE = {
  title: "Security Agent DevLog",
  description: "SKT ALEPH 보안 자동화 및 AI 에이전트 툴체인 기술 의사결정 로그",
  author: "mmmphyun",
  language: "ko",
  locale: "ko-KR",
  url: "https://mmmphyun.github.io",
  basePath: "/security-agent-toolkit",
  brand: {
    name: "security",
    accent: "devlog",
  },
  socialLinks: [
    {
      label: "GitHub",
      href: "https://github.com/mmmphyun/security-agent-toolkit",
    },
    {
      label: "RSS",
      href: "/rss.xml",
    },
  ],
  storagePrefix: "astro-bento-blog",
  features: {
    transitions: true,
  },
} as const;

export const GENERATE_SLUG_FROM_TITLE = true;

// Named exports keep imports concise throughout the theme.
export const SITE_TITLE = SITE.title;
export const SITE_DESCRIPTION = SITE.description;
export const TRANSITION_API = SITE.features.transitions;
