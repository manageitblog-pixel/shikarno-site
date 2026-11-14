import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { Bait, Wordmark, C, FONT } from "./brand";
import { fontCss } from "./parts";
import LOGOS from "./logos.json";

// Обкладинки v4 (власник 14.11 «глянь Ігора»: вставки-логотипи, без пустого місця, текст знизу з плашкою, серія зверху).
// Логотипи — simple-icons (CC0), бренди — лише як позначення продукту, про який ролик.
const L = LOGOS as Record<string, { path: string; hex: string }>;
export const Logo: React.FC<{ id: string; size: number; tile?: boolean; rot?: number }> = ({ id, size, tile = true, rot = 0 }) => {
  const l = L[id]; if (!l) return null;
  const svg = <svg viewBox="0 0 24 24" width={tile ? size * 0.62 : size} height={tile ? size * 0.62 : size}><path d={l.path} fill={l.hex} /></svg>;
  if (!tile) return svg;
  return <div style={{ width: size, height: size, borderRadius: size * 0.24, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 24px 50px rgba(0,0,0,0.45)", transform: `rotate(${rot}deg)`, border: "4px solid rgba(255,255,255,0.9)" }}>{svg}</div>;
};

type P = { series: string; text: string; logos?: string[]; keys?: string[]; mood?: "talk" | "happy" | "judge" | "shock";
  shot?: string; c1?: string; c2?: string; big?: string; wide?: boolean };

export const Thumb4: React.FC<P> = (p) => {
  const c1 = p.c1 ?? "#1E6BFF", c2 = p.c2 ?? "#FF4F8B";
  const parts = p.text.split("*");
  const words = (size: number) => (
    <div style={{ color: "#fff", fontWeight: 900, fontSize: size, lineHeight: 0.98, letterSpacing: -2, textTransform: "uppercase", textShadow: "0 8px 0 rgba(0,0,0,0.45), 0 0 40px rgba(0,0,0,0.6)" }}>
      {parts.map((t, i) => i % 2 ? <span key={i} style={{ background: C.yellow, color: "#0E0B24", padding: "0 16px", borderRadius: 14, display: "inline-block", textShadow: "none", transform: "rotate(-1.5deg)" }}>{t}</span> : <span key={i}>{t}</span>)}
    </div>
  );
  const bg = (
    <>
      <div style={{ position: "absolute", inset: 0, background: `linear-gradient(115deg, ${c1} 0%, ${c1} 48%, ${c2} 52%, ${c2} 100%)` }} />
      {p.shot && <Img src={staticFile(p.shot)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.28, filter: "blur(2px) saturate(1.2)", mixBlendMode: "luminosity" }} />}
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 75% 35%, rgba(255,255,255,0.18), transparent 45%), linear-gradient(0deg, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.15) 45%, rgba(0,0,0,0) 70%)" }} />
    </>
  );
  const series = <div style={{ position: "absolute", left: 40, top: 36, background: C.yellow, color: "#0E0B24", fontWeight: 900, fontSize: 46, padding: "8px 22px", borderRadius: 10, letterSpacing: 1 }}>{p.series}</div>;
  const logos = p.logos ?? [];
  const keys = p.keys?.length ? (
    <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
      {p.keys.map((k, i) => <div key={i} style={{ background: "rgba(14,11,36,0.85)", color: "#fff", fontWeight: 800, fontSize: 56, padding: "10px 28px", borderRadius: 40, border: "3px solid rgba(255,255,255,0.35)" }}>{k}</div>)}
    </div>
  ) : null;

  if (p.wide) return (
    <AbsoluteFill style={{ fontFamily: FONT, overflow: "hidden" }}>
      <style>{fontCss}</style>{bg}{series}
      {/* логотипи — верхня права зона */}
      <div style={{ position: "absolute", right: 70, top: 90, display: "flex", gap: 34 }}>
        {logos.map((id, i) => <Logo key={id} id={id} size={logos.length > 2 ? 250 : 320} rot={i % 2 ? 6 : -6} />)}
      </div>
      {p.big && <div style={{ position: "absolute", right: 70, top: logos.length ? 330 : 120, color: C.yellow, fontWeight: 900, fontSize: 230, lineHeight: 0.9, WebkitTextStroke: "6px #0E0B24", paintOrder: "stroke fill", transform: "rotate(-4deg)" }}>{p.big}</div>}
      {/* Байт — праворуч знизу */}
      <div style={{ position: "absolute", right: 70, bottom: -110, transform: "rotate(-5deg)", filter: "drop-shadow(0 30px 50px rgba(0,0,0,0.6))" }}><Bait size={p.big ? 420 : 520} mood={p.mood ?? "shock"} /></div>
      {/* ключі + текст — ліва нижня зона */}
      <div style={{ position: "absolute", left: 50, top: 150, width: 820 }}>{keys}</div>
      <div style={{ position: "absolute", left: 50, bottom: 110, width: 1250 }}>{words(150)}</div>
      <div style={{ position: "absolute", left: 50, bottom: 34 }}><Wordmark size={46} /></div>
    </AbsoluteFill>
  );
  return (
    <AbsoluteFill style={{ fontFamily: FONT, overflow: "hidden" }}>
      <style>{fontCss}</style>{bg}{series}
      <div style={{ position: "absolute", left: 0, right: 0, top: 170, display: "flex", justifyContent: "center", gap: 30 }}>
        {logos.map((id, i) => <Logo key={id} id={id} size={logos.length > 2 ? 230 : 300} rot={i % 2 ? 6 : -6} />)}
      </div>
      {p.big && <div style={{ position: "absolute", left: 0, right: 0, top: 520, textAlign: "center", color: C.yellow, fontWeight: 900, fontSize: 260, lineHeight: 0.9, WebkitTextStroke: "6px #0E0B24", paintOrder: "stroke fill" }}>{p.big}</div>}
      <div style={{ position: "absolute", left: 50, right: 50, top: p.big ? 800 : 560 }}>{keys}</div>
      <div style={{ position: "absolute", left: 50, right: 50, top: p.big ? 900 : 700 }}>{words(150)}</div>
      <div style={{ position: "absolute", right: -60, bottom: -90, transform: "rotate(8deg)", filter: "drop-shadow(0 30px 50px rgba(0,0,0,0.6))" }}><Bait size={640} mood={p.mood ?? "shock"} /></div>
      <div style={{ position: "absolute", left: 50, bottom: 50 }}><Wordmark size={50} /></div>
    </AbsoluteFill>
  );
};
