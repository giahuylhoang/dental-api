import Link from "next/link";

export interface AvatarProps {
  name: string;
  size?: number;
  seed?: string;
  href?: string;
}

const COLORS = [
  "bg-blue-600", "bg-green-700", "bg-amber-700",
  "bg-blue-800", "bg-slate-900", "bg-red-800", "bg-slate-600",
];

function hashColor(key: string): string {
  let hash = 0;
  for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) & 0xffffffff;
  return COLORS[Math.abs(hash) % COLORS.length];
}

// Size map: default 36px → w-9 h-9 text-sm
const SIZE_CLASS: Record<number, string> = {
  24: "w-6 h-6 text-xs",
  32: "w-8 h-8 text-xs",
  36: "w-9 h-9 text-sm",
  40: "w-10 h-10 text-sm",
  48: "w-12 h-12 text-base",
};

export function Avatar({ name, size = 36, seed, href }: AvatarProps) {
  const initials = (name || "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 3)
    .map((w) => w[0].toUpperCase())
    .join("");
  const bg = hashColor(seed || name || "");
  const sizeClass = SIZE_CLASS[size] ?? "w-9 h-9 text-sm";

  const circle = (
    <div className={`inline-flex items-center justify-center rounded-full text-white font-semibold shrink-0 ${bg} ${sizeClass}`}>
      {initials}
    </div>
  );

  if (href) return <Link href={href} className="no-underline">{circle}</Link>;
  return circle;
}
