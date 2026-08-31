// Petites icones SVG inline (pas de dependance externe), trait 1.75, 20x20.
type IconProps = { className?: string };

const base = { fill: "none", stroke: "currentColor", strokeWidth: 1.75, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export function IconDashboard({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" className={className} {...base}>
      <rect x="2.5" y="2.5" width="6.5" height="7.5" rx="1.5" />
      <rect x="11" y="2.5" width="6.5" height="4.5" rx="1.5" />
      <rect x="11" y="9" width="6.5" height="8.5" rx="1.5" />
      <rect x="2.5" y="12" width="6.5" height="5.5" rx="1.5" />
    </svg>
  );
}

export function IconUsers({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" className={className} {...base}>
      <circle cx="7" cy="6.5" r="2.75" />
      <path d="M2 17c0-2.9 2.24-5 5-5s5 2.1 5 5" />
      <circle cx="14.5" cy="7.5" r="2.1" />
      <path d="M12.8 12.3c2.1.3 3.7 2.1 3.7 4.7" />
    </svg>
  );
}

export function IconToken({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" className={className} {...base}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M10 6.5v7M7.75 8.25c0-1 1-1.75 2.25-1.75s2.25.6 2.25 1.5c0 2-4.5 1-4.5 3 0 .9 1 1.5 2.25 1.5s2.25-.6 2.25-1.5" />
    </svg>
  );
}

export function IconCall({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" className={className} {...base}>
      <path d="M3.5 4c0-.6.5-1 1-1H6.8c.5 0 .9.3 1 .8l.7 2.7c.1.4 0 .9-.4 1.2l-1.4 1.2c1 2.1 2.7 3.8 4.8 4.8l1.2-1.4c.3-.3.7-.4 1.1-.3l2.7.7c.5.1.8.5.8 1v2.3c0 .6-.5 1-1 1H16C9 17 3.5 11.5 3.5 4.5V4Z" />
    </svg>
  );
}

export function IconStats({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" className={className} {...base}>
      <path d="M3 17V8M8.5 17V3M14 17v-6M18 17H2" />
    </svg>
  );
}

export function IconLogout({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" className={className} {...base}>
      <path d="M8 3H4.5c-.6 0-1 .4-1 1v12c0 .6.4 1 1 1H8M13.5 14l3.5-4-3.5-4M17 10H7" />
    </svg>
  );
}

export function IconDownload({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="16" height="16" className={className} {...base}>
      <path d="M10 3v10M6 9.5 10 13.5 14 9.5M4 17h12" />
    </svg>
  );
}

export function IconPlus({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="16" height="16" className={className} {...base}>
      <path d="M10 4v12M4 10h12" />
    </svg>
  );
}

export function IconPhone({ className }: IconProps) {
  return <IconCall className={className} />;
}

export function IconWallet({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" className={className} {...base}>
      <rect x="2.5" y="5" width="15" height="11" rx="2" />
      <path d="M2.5 8.5h15M13.5 12.5h2" />
    </svg>
  );
}
