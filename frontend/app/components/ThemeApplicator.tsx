"use client";

import { useEffect, useState, createContext, useContext } from "react";

export interface CustomizationSettings {
  font_family: string;
  font_size_scale: string;
  logo_url: string;
  favicon_url: string;
  hero_title: string;
  hero_subtitle: string;
}

export const DEFAULT_CUSTOMIZATION: CustomizationSettings = {
  font_family: "Inter",
  font_size_scale: "16px",
  logo_url: "/logo.svg",
  favicon_url: "/favicon.svg",
  hero_title: "RAVEN AI",
  hero_subtitle: "AI Business Development Agent",
};

const CustomizationContext = createContext<CustomizationSettings>(DEFAULT_CUSTOMIZATION);

export const useCustomization = () => useContext(CustomizationContext);

export function ThemeApplicator({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<CustomizationSettings>(DEFAULT_CUSTOMIZATION);

  const applyCustomization = (config: Partial<CustomizationSettings>) => {
    const updated = { ...DEFAULT_CUSTOMIZATION, ...config };
    setTheme(updated);

    // Save to localStorage for instant client rendering
    try {
      localStorage.setItem("reach_customization", JSON.stringify(updated));
    } catch {}

    // 1. Font Family & Google Fonts Loading
    const fontName = updated.font_family || "Inter";
    if (fontName !== "System Default" && fontName !== "Inter") {
      const linkId = "custom-google-font";
      let linkEl = document.getElementById(linkId) as HTMLLinkElement;
      if (!linkEl) {
        linkEl = document.createElement("link");
        linkEl.id = linkId;
        linkEl.rel = "stylesheet";
        document.head.appendChild(linkEl);
      }
      const formattedFont = fontName.replace(/ /g, "+");
      linkEl.href = `https://fonts.googleapis.com/css2?family=${formattedFont}:wght@300;400;500;600;700;800;900&display=swap`;
    }

    if (fontName === "System Default") {
      document.body.style.fontFamily = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    } else {
      document.body.style.fontFamily = `'${fontName}', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
    }

    // 2. Base Font Size Scale
    if (updated.font_size_scale) {
      document.documentElement.style.fontSize = updated.font_size_scale;
    }

    // 3. Favicon & Document Title
    if (updated.hero_title) {
      document.title = `${updated.hero_title} — ${updated.hero_subtitle || "AI Business Development Agent"}`;
    }

    if (updated.favicon_url) {
      const rels = ["icon", "shortcut icon", "apple-touch-icon"];
      rels.forEach((rel) => {
        let iconLink = document.querySelector(`link[rel='${rel}']`) as HTMLLinkElement;
        if (!iconLink) {
          iconLink = document.createElement("link");
          iconLink.rel = rel;
          document.head.appendChild(iconLink);
        }
        iconLink.href = updated.favicon_url;
      });
    }
  };

  useEffect(() => {
    // Check cached localStorage first for instant render
    try {
      const cached = localStorage.getItem("reach_customization");
      if (cached) {
        applyCustomization(JSON.parse(cached));
      }
    } catch {}

    // Fetch latest configuration from API via relative route proxied by Next.js
    fetch("/api/v1/config/public")
      .then((res) => res.json())
      .then((data) => {
        const homeConfig = (data.providers || []).find(
          (p: any) => p.provider_name === "home_customization"
        );
        if (homeConfig && homeConfig.config_data) {
          applyCustomization(homeConfig.config_data);
        }
      })
      .catch(() => {
        /* ignore fallback */
      });
  }, []);

  return (
    <CustomizationContext.Provider value={theme}>
      {children}
    </CustomizationContext.Provider>
  );
}
