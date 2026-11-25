import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame } from "remotion";
import { Bait, Wordmark, C, FONT } from "./brand";
import { fontCss } from "./parts";

/* IG Reel без голосу (25.11, ліміт TTS): «3 промпти з гайду ChatGPT».
   Усе важливе — у кропі сітки 3:4 (y 240–1680). Кадр 0 — повний, нерухомий гачок (обкладинка). */
export type IgPromptsData = {
  total: number; hookEnd: number; per: number; hook: string; model: string;
  prompts: { title: string; text: string }[];
  outro: { a: string; b: string };
};

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const sp = (f: number, d = 12) => spring({ frame: f, fps: 30, config: { damping: d, mass: 0.7 } });
const hl = (t: string, color: string) => t.split(/(\*[^*]+\*)/g).filter(Boolean)
  .map((x, i) => x.startsWith("*") ? <span key={i} style={{ background: color, color: C.ink, padding: "0 14px", borderRadius: 16 }}>{x.slice(1, -1)}</span> : <span key={i}>{x}</span>);
const brackets = (t: string) => t.split(/(\[[^\]]+\])/g).filter(Boolean)
  .map((x, i) => x.startsWith("[") ? <span key={i} style={{ color: C.yellow }}>{x}</span> : <span key={i}>{x}</span>);

const Bg: React.FC = () => (
  <AbsoluteFill style={{ background: `linear-gradient(160deg, ${C.bg1} 0%, ${C.bg2} 100%)` }}>
    <AbsoluteFill style={{ background: `radial-gradient(circle at 80% 20%, ${C.purple}33, transparent 45%), radial-gradient(circle at 15% 85%, ${C.pink}26, transparent 45%)` }} />
  </AbsoluteFill>
);

const BrandPill: React.FC<{ label: string }> = ({ label }) => (
  <div style={{ position: "absolute", top: 270, left: 0, right: 0, display: "flex", justifyContent: "center", alignItems: "center", gap: 22 }}>
    <Wordmark size={54} />
    <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 36, color: C.ink, background: C.cyan, padding: "6px 22px", borderRadius: 14, letterSpacing: 1 }}>{label}</div>
  </div>
);

export const IgPrompts: React.FC<IgPromptsData> = (p) => {
  const f = useCurrentFrame();
  const outroFrom = p.hookEnd + p.per * p.prompts.length;
  const idx = f < p.hookEnd ? -1 : f >= outroFrom ? 99 : Math.floor((f - p.hookEnd) / p.per);

  /* --- 0. гачок: кадр 0 повний і нерухомий; рух лише з кадру 4 --- */
  if (idx === -1) {
    const pulse = f < 4 ? 1 : 1 + 0.02 * Math.sin((f - 4) / 5);
    return (
      <AbsoluteFill style={{ fontFamily: FONT }}>
        <style>{fontCss}</style>
        <Bg />
        <BrandPill label="ГАЙД #1" />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: 960, textAlign: "center", fontWeight: 900, fontSize: 112, lineHeight: 1.12, color: "white", letterSpacing: -2, marginTop: -120, scale: `${pulse}` }}>
            {hl(p.hook, C.yellow)}
          </div>
        </AbsoluteFill>
        <div style={{ position: "absolute", top: 1330, left: 90, fontFamily: FONT, fontWeight: 900, fontSize: 44, color: C.ink, background: C.pink, padding: "10px 26px", borderRadius: 16, rotate: "-4deg" }}>
          ЗБЕРЕЖИ
        </div>
        <div style={{ position: "absolute", top: 1240, right: 90 }}><Bait size={260} mood="happy" frameOffset={0} /></div>
      </AbsoluteFill>
    );
  }

  /* --- фінал --- */
  if (idx === 99) {
    const t = f - outroFrom;
    const k = sp(t, 12);
    const row = (text: string, c: string, i: number) => {
      const a = Math.min(1, Math.max(0, (t - 8 - i * 8) / 10));
      return <div style={{ width: 960, padding: "26px 30px", borderRadius: 30, background: "rgba(14,11,36,0.8)", border: `4px solid ${c}`, boxShadow: `0 0 30px ${c}55`,
        fontFamily: FONT, fontWeight: 900, fontSize: 46, lineHeight: 1.25, color: "white", textAlign: "center", opacity: a, transform: `translateY(${(1 - a) * 40}px)` }}>{hl(text, c)}</div>;
    };
    return (
      <AbsoluteFill style={{ fontFamily: FONT }}>
        <style>{fontCss}</style>
        <Bg />
        <AbsoluteFill style={{ alignItems: "center", paddingTop: 330, gap: 40 }}>
          <div style={{ scale: `${k}` }}><Bait size={280} withBody mood="happy" /></div>
          <div style={{ scale: `${k}` }}><Wordmark size={100} /></div>
          {row(p.outro.a, "#FF0033", 0)}
          {row(p.outro.b, "#2AABEE", 1)}
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  /* --- промпт i --- */
  const pr = p.prompts[idx];
  const t = f - p.hookEnd - idx * p.per;
  const inK = sp(t, 13);
  const typeTo = 28;
  const shown = pr.text.slice(0, Math.round(interpolate(t, [4, typeTo], [0, pr.text.length], clamp)));
  const outK = interpolate(t, [p.per - 6, p.per], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ fontFamily: FONT }}>
      <style>{fontCss}</style>
      <Bg />
      <BrandPill label={`ПРОМПТ ${idx + 1}/${p.prompts.length}`} />
      <div style={{ position: "absolute", top: 370, left: 0, right: 0, textAlign: "center", fontWeight: 900, fontSize: 104, color: "white", letterSpacing: -2, opacity: outK,
        scale: `${0.85 + 0.15 * inK}` }}>
        {hl(`*${pr.title}*`, C.yellow)}
      </div>
      <div style={{ position: "absolute", top: 540, left: 60, width: 960, padding: "34px 36px 36px", borderRadius: 44, background: "#111116", border: "2px solid #2E2E3A",
        display: "flex", flexDirection: "column", gap: 22, opacity: inK * outK, transform: `translateY(${(1 - inK) * 60}px)` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, fontWeight: 800, fontSize: 30, color: "#9A9AA8" }}>
          <div style={{ width: 18, height: 18, borderRadius: 9, background: C.cyan }} />{p.model}
        </div>
        <div style={{ alignSelf: "flex-end", maxWidth: 880, padding: "26px 32px", borderRadius: 30, background: "#1F1F27", border: `3px solid ${C.purple}`,
          fontWeight: 700, fontSize: 52, lineHeight: 1.3, color: "white" }}>
          {brackets(shown)}<span style={{ opacity: t < typeTo && Math.floor(t / 6) % 2 ? 1 : 0, color: C.yellow }}>|</span>
        </div>
      </div>
      <div style={{ position: "absolute", top: 1500, left: 70, fontWeight: 800, fontSize: 40, color: "#C9C2FF", opacity: outK }}>
        заміни <span style={{ color: C.yellow }}>[дужки]</span> на своє
      </div>
      <div style={{ position: "absolute", top: 1390, right: 70 }}><Bait size={200} mood="talk" mouth={0} /></div>
      {/* прогрес */}
      <div style={{ position: "absolute", top: 1600, left: 70, display: "flex", gap: 14 }}>
        {p.prompts.map((_, i) => <div key={i} style={{ width: i === idx ? 90 : 40, height: 14, borderRadius: 7, background: i <= idx ? C.yellow : "#3A3560" }} />)}
      </div>
    </AbsoluteFill>
  );
};
