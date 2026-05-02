export interface RecentItem {
  kind: 'patient' | 'invoice' | 'appointment';
  id: string;
  label: string;
  visitedAt: number;
}

const KEY = 'pms.recentlyViewed';
const MAX = 10;

function read(): RecentItem[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]');
  } catch {
    return [];
  }
}

function write(items: RecentItem[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    // ignore (private mode / SSR)
  }
}

export function markVisited(kind: RecentItem['kind'], id: string, label: string) {
  const items = read().filter((i) => !(i.kind === kind && i.id === id));
  items.unshift({ kind, id, label, visitedAt: Date.now() });
  write(items.slice(0, MAX));
}

export function getRecent(): RecentItem[] {
  return read();
}
