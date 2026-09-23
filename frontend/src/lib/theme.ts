import { useCallback, useEffect, useState } from "react";

export type Theme = "system" | "light" | "dark";

const STORAGE_KEY = "amd.theme";

function readTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

function persistTheme(theme: Theme) {
  try {
    if (theme === "system") localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    return;
  }
}

function applyTheme(theme: Theme) {
  if (theme === "system") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", theme);
}

export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setThemeState] = useState<Theme>(readTheme);

  useEffect(() => applyTheme(theme), [theme]);

  const setTheme = useCallback((next: Theme) => {
    persistTheme(next);
    setThemeState(next);
  }, []);

  return [theme, setTheme];
}
