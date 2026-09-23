const relative = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
const dateFormat = new Intl.DateTimeFormat("en", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 31_536_000],
  ["month", 2_592_000],
  ["week", 604_800],
  ["day", 86_400],
  ["hour", 3_600],
  ["minute", 60],
];

export function timeAgo(value: string, now = Date.now()): string {
  const seconds = Math.round((new Date(value).getTime() - now) / 1000);
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) return relative.format(Math.round(seconds / size), unit);
  }
  return "just now";
}

export function formatDate(value: string): string {
  return dateFormat.format(new Date(value));
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export type Bucket = "Today" | "Yesterday" | "Previous 7 days" | "Older";

export function dayBucket(value: string, now = new Date()): Bucket {
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const time = new Date(value).getTime();
  if (time >= startOfToday) return "Today";
  if (time >= startOfToday - 86_400_000) return "Yesterday";
  if (time >= startOfToday - 7 * 86_400_000) return "Previous 7 days";
  return "Older";
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return (
    (parts[0]?.[0] ?? "") + (parts.length > 1 ? (parts.at(-1)?.[0] ?? "") : "")
  ).toUpperCase();
}
