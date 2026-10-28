import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

export const C = {
  yellow: "#FFD60A",
  purple: "#7C5CFF",
  pink: "#FF4F8B",
  cyan: "#4CF2FF",
  ink: "#0E0B24",
  bg1: "#0B0A1C",
  bg2: "#1A1240",
};
export const FONT = "Mont";

/* ---------- Ведучий «Байт» ---------- */
type Mood = "talk" | "happy" | "judge";
export const Bait: React.FC<{ size?: number; mouth?: number; mood?: Mood; look?: number; frameOffset?: number; withBody?: boolean }> = ({
  size = 240, mouth = 0, mood = "talk", look = 0, frameOffset = 0, withBody = false,
}) => {
  const f = useCurrentFrame() + frameOffset;
  // моргання кожні ~3.3 с
  const cyc = f % 100;
  const blink = cyc > 94 ? interpolate(cyc, [94, 97, 100], [1, 0.1, 1]) : 1;
  const bob = Math.sin(f / 9) * 4;
  const ant = Math.sin(f / 7) * 8;
  const mw = 30 + 14 * mouth;
  const mh = 5 + 24 * mouth;
  const eyeRy = mood === "happy" ? 6 : 16 * blink;
  const vbH = withBody ? 300 : 200;
  return (
    <svg width={size} height={(size * vbH) / 200} viewBox={`0 0 200 ${vbH}`} style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id="baitHead" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={C.purple} />
          <stop offset="1" stopColor={C.pink} />
        </linearGradient>
        <filter id="baitGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <g transform={`translate(0 ${bob})`}>
        {/* антена */}
        <g transform={`rotate(${ant} 100 44)`}>
          <line x1="100" y1="44" x2="100" y2="16" stroke="#C9C2FF" strokeWidth="6" strokeLinecap="round" />
          <circle cx="100" cy="12" r="11" fill={C.yellow} filter="url(#baitGlow)" />
        </g>
        {/* вуха */}
        <rect x="6" y="86" width="20" height="44" rx="8" fill={C.yellow} />
        <rect x="174" y="86" width="20" height="44" rx="8" fill={C.yellow} />
        {/* голова */}
        <rect x="18" y="40" width="164" height="136" rx="44" fill="url(#baitHead)" />
        <rect x="34" y="56" width="132" height="104" rx="30" fill={C.ink} />
        {/* брови для вердикту */}
        {mood === "judge" && (
          <>
            <rect x="58" y="70" width="32" height="6" rx="3" fill={C.cyan} transform="rotate(12 74 73)" />
            <rect x="110" y="70" width="32" height="6" rx="3" fill={C.cyan} transform="rotate(-12 126 73)" />
          </>
        )}
        {/* очі */}
        <g filter="url(#baitGlow)">
          {mood === "happy" ? (
            <>
              <path d={`M${62 + look} 102 Q${75 + look} 86 ${88 + look} 102`} stroke={C.cyan} strokeWidth="8" fill="none" strokeLinecap="round" />
              <path d={`M${112 + look} 102 Q${125 + look} 86 ${138 + look} 102`} stroke={C.cyan} strokeWidth="8" fill="none" strokeLinecap="round" />
            </>
          ) : (
            <>
              <ellipse cx={75 + look} cy="98" rx="13" ry={eyeRy} fill={C.cyan} />
              <ellipse cx={125 + look} cy="98" rx="13" ry={eyeRy} fill={C.cyan} />
            </>
          )}
          {/* рот */}
          <rect x={100 - mw / 2} y={134 - mh / 2} width={mw} height={mh} rx={Math.min(mh, mw) / 2} fill={C.cyan} />
        </g>
        {/* щічки */}
        <circle cx="52" cy="128" r="8" fill={C.pink} opacity="0.55" />
        <circle cx="148" cy="128" r="8" fill={C.pink} opacity="0.55" />
        {withBody && (
          <>
            <rect x="84" y="174" width="32" height="16" fill="#C9C2FF" />
            <rect x="40" y="186" width="120" height="100" rx="34" fill="url(#baitHead)" />
            <rect x="70" y="210" width="60" height="44" rx="14" fill={C.ink} />
            <text x="100" y="242" textAnchor="middle" fontFamily={FONT} fontWeight="900" fontSize="26" fill={C.yellow}>ШІ</text>
          </>
        )}
      </g>
    </svg>
  );
};

/* ---------- Логотип-слово ---------- */
export const Wordmark: React.FC<{ size?: number }> = ({ size = 80 }) => (
  <div style={{ display: "flex", alignItems: "center", fontFamily: FONT, fontWeight: 900, fontSize: size, letterSpacing: -size * 0.02, skewX: "-6deg" } as React.CSSProperties}>
    <span style={{ background: C.yellow, color: C.ink, padding: `0 ${size * 0.14}px`, borderRadius: size * 0.18, marginRight: size * 0.04, lineHeight: 1.12 }}>ШІ</span>
    <span style={{ color: "white", lineHeight: 1.12 }}>карно</span>
  </div>
);

/* ---------- Аватар каналу ---------- */
export const Avatar: React.FC<{ size?: number }> = ({ size = 120 }) => (
  <div style={{
    width: size, height: size, borderRadius: size / 2, background: `radial-gradient(circle at 30% 25%, #3B2A8F, ${C.ink} 70%)`,
    display: "flex", alignItems: "center", justifyContent: "center", border: `${Math.max(2, size * 0.035)}px solid ${C.yellow}`, overflow: "hidden",
  }}>
    <div style={{ marginTop: size * 0.08 }}><Bait size={size * 0.74} /></div>
  </div>
);

/* ---------- соцмережі (кінцева картка; 28.10 — на прохання власника в кожному ролику) ---------- */
export const Socials: React.FC<{ scale?: number; t?: number }> = ({ scale = 1, t = 99 }) => {
  const rows: [string, string, string][] = [
    ["YouTube", "@shikarno_ua", "#FF0033"],
    ["TikTok", "@shikarno_ai_ua", "#25F4EE"],
    ["Telegram", "@shikarno_ai_ua", "#2AABEE"],
    ["Сайт", "shikarno.com.ua", "#FFD60A"],
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 * scale, alignItems: "stretch", width: 760 * scale }}>
      {rows.map(([n, h, c], i) => {
        const a = Math.min(1, Math.max(0, (t - i * 5) / 8));
        return (
          <div key={n} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 20, padding: `${14 * scale}px ${28 * scale}px`, borderRadius: 30 * scale,
            background: "rgba(14,11,36,0.75)", border: `${3 * scale}px solid ${c}`, boxShadow: `0 0 ${24 * scale}px ${c}55`, opacity: a, transform: `translateX(${(1 - a) * 120}px)` }}>
            <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 38 * scale, color: c }}>{n}</span>
            <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 42 * scale, color: "white" }}>{h}</span>
          </div>
        );
      })}
    </div>
  );
};
