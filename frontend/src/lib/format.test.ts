import { dayBucket, formatBytes, initials, timeAgo } from "./format";

test("formats byte sizes", () => {
  expect(formatBytes(512)).toBe("512 B");
  expect(formatBytes(2048)).toBe("2.0 KB");
  expect(formatBytes(3.5 * 1024 * 1024)).toBe("3.5 MB");
});

test("describes times relative to now", () => {
  const now = new Date("2026-09-23T12:00:00Z").getTime();
  expect(timeAgo("2026-09-23T11:59:30Z", now)).toBe("just now");
  expect(timeAgo("2026-09-23T09:00:00Z", now)).toBe("3 hours ago");
  expect(timeAgo("2026-09-21T12:00:00Z", now)).toBe("2 days ago");
});

test("groups conversations by day", () => {
  const now = new Date(2026, 8, 23, 15, 0);
  expect(dayBucket(new Date(2026, 8, 23, 9, 0).toISOString(), now)).toBe("Today");
  expect(dayBucket(new Date(2026, 8, 22, 23, 0).toISOString(), now)).toBe("Yesterday");
  expect(dayBucket(new Date(2026, 8, 18).toISOString(), now)).toBe("Previous 7 days");
  expect(dayBucket(new Date(2026, 6, 1).toISOString(), now)).toBe("Older");
});

test("builds initials from names", () => {
  expect(initials("Ada Lovelace")).toBe("AL");
  expect(initials("Plato")).toBe("P");
  expect(initials("Mary Jane Watson")).toBe("MW");
});
