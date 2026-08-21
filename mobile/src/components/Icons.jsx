// Small inline-SVG icon set. Deliberately not an icon-font/library dependency
// - each icon is a tiny functional component so there's nothing new to
// install, nothing to keep in sync with a CDN, and each one is easy to tweak.
// Every icon accepts the usual svg props (size defaults to 16) plus className.

function Base({ size = 16, children, ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...rest}
    >
      {children}
    </svg>
  );
}

export function IconMoon(props) {
  return (
    <Base {...props}>
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </Base>
  );
}

export function IconHeart(props) {
  return (
    <Base {...props}>
      <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z" />
    </Base>
  );
}

export function IconActivity(props) {
  return (
    <Base {...props}>
      <path d="M3 12h4l3 8 4-16 3 8h4" />
    </Base>
  );
}

export function IconTrendingUp(props) {
  return (
    <Base {...props}>
      <path d="M3 17l5-5 4 4 8-9" />
      <path d="M15 7h5v5" />
    </Base>
  );
}

export function IconScale(props) {
  return (
    <Base {...props}>
      <path d="M12 3v3M7 6h10M5 21h14" />
      <path d="M5 10l2-4 2 4a2.2 2.2 0 0 1-4 0z" />
      <path d="M15 10l2-4 2 4a2.2 2.2 0 0 1-4 0z" />
      <path d="M9 21v-4a3 3 0 0 1 6 0v4" />
    </Base>
  );
}

export function IconArrowRight(props) {
  return (
    <Base {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </Base>
  );
}

export function IconUtensils(props) {
  return (
    <Base {...props}>
      <path d="M12 3v18M5 8l7-5 7 5" />
    </Base>
  );
}

export function IconRefresh(props) {
  return (
    <Base {...props}>
      <path d="M20 12a8 8 0 1 1-2.34-5.66" />
      <path d="M20 4v5h-5" />
    </Base>
  );
}

export function IconHome(props) {
  return (
    <Base {...props}>
      <path d="M3 11l9-7 9 7" />
      <path d="M5 10v9h14v-9" />
    </Base>
  );
}

export function IconDumbbell(props) {
  return (
    <Base {...props}>
      <path d="M6 5v14M18 5v14M4 9h4M4 15h4M16 9h4M16 15h4" />
    </Base>
  );
}

export function IconClock(props) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 2" />
    </Base>
  );
}

export function IconSettingsGear(props) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.55V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1-1.55 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1 0-4h.09a1.7 1.7 0 0 0 1.55-1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H9a1.7 1.7 0 0 0 1-1.55V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V9a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.55 1z" />
    </Base>
  );
}

export function IconCloudRain(props) {
  return (
    <Base {...props}>
      <path d="M20 16.2A5 5 0 0 0 18 7h-1.3A7 7 0 1 0 5 14.5" />
      <path d="M12 12v6M9 15h6" />
    </Base>
  );
}

export function IconVirus(props) {
  return (
    <Base {...props}>
      <path d="M12 21s-7-4.5-9-9a5 5 0 0 1 9-4 5 5 0 0 1 9 4c-2 4.5-9 9-9 9z" />
    </Base>
  );
}

export function IconBandage(props) {
  return (
    <Base {...props}>
      <path d="M6 4v16M18 4v16M6 12h12" />
    </Base>
  );
}

export function IconTarget(props) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </Base>
  );
}

export function IconBike(props) {
  return (
    <Base {...props}>
      <circle cx="6" cy="17" r="3" />
      <circle cx="18" cy="17" r="3" />
      <path d="M9 17h6l-3-9-3 4h6M12 8h3l2 5" />
    </Base>
  );
}

export function IconIndoor(props) {
  return (
    <Base {...props}>
      <rect x="4" y="4" width="16" height="16" rx="2" />
    </Base>
  );
}
