import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { Bait, Wordmark, C, FONT } from "./brand";
import { fontCss } from "./parts";

// Обкладинки v3 (14.11, docs/video-principles.md «Обкладинки»): ОДИН конкретний об'єкт у фокусі + емоція Байта + ≤3 слова інтриги
// (не дублюють назву). Темний фон з одним акцентом — щоб об'єкт і текст читались розміром з ніготь.
// object: card | toggle | big | shot. wide=true → 1920×1080.
type P = { object: "card" | "toggle" | "big" | "shot"; text: string; accent?: string; mood?: "talk" | "happy" | "judge" | "shock";
  label?: string; big?: string; shot?: string; on?: boolean; wide?: boolean };

const Card: React.FC<{ w: number; label?: string }> = ({ w, label }) => (
  <div style={{ width: w, height: w * 0.63, borderRadius: w * 0.06, background: "linear-gradient(135deg,#2B2B2B 0%,#0E0E10 60%,#3A3A3A 100%)", boxShadow: "0 50px 100px rgba(0,0,0,0.7), inset 0 2px 0 rgba(255,255,255,0.15)", position: "relative", border: "2px solid rgba(255,255,255,0.12)" }}>
    <div style={{ position: "absolute", left: w * 0.08, top: w * 0.2, width: w * 0.14, height: w * 0.11, borderRadius: w * 0.02, background: "linear-gradient(135deg,#F5D27A,#B8902E)" }} />
    <div style={{ position: "absolute", left: w * 0.08, top: w * 0.4, color: "#E8E8E8", fontFamily: "monospace", fontWeight: 700, fontSize: w * 0.075, letterSpacing: w * 0.012 }}>•••• •••• •••• 4821</div>
    {label && <div style={{ position: "absolute", right: w * 0.07, top: w * 0.07, color: "#fff", fontWeight: 900, fontSize: w * 0.06, letterSpacing: 2 }}>{label}</div>}
    <div style={{ position: "absolute", right: w * 0.07, bottom: w * 0.06, display: "flex" }}>
      <div style={{ width: w * 0.11, height: w * 0.11, borderRadius: "50%", background: "#EB001B", opacity: 0.9 }} />
      <div style={{ width: w * 0.11, height: w * 0.11, borderRadius: "50%", background: "#F79E1B", opacity: 0.9, marginLeft: -w * 0.045 }} />
    </div>
  </div>
);

const Toggle: React.FC<{ w: number; label?: string; on?: boolean }> = ({ w, label, on = true }) => (
  <div style={{ width: w, borderRadius: w * 0.05, background: "#fff", padding: `${w * 0.06}px ${w * 0.06}px`, display: "flex", alignItems: "center", gap: w * 0.05, boxShadow: "0 50px 100px rgba(0,0,0,0.6)", fontFamily: "Arial, sans-serif" }}>
    <div style={{ flex: 1, color: "#111", fontWeight: 700, fontSize: w * 0.065, lineHeight: 1.15 }}>{label}</div>
    <div style={{ width: w * 0.22, height: w * 0.12, borderRadius: w * 0.06, background: on ? "#19C37D" : "#ccc", position: "relative", flexShrink: 0 }}>
      <div style={{ position: "absolute", top: w * 0.012, left: on ? w * 0.112 : w * 0.012, width: w * 0.096, height: w * 0.096, borderRadius: "50%", background: "#fff", boxShadow: "0 3px 8px rgba(0,0,0,0.3)" }} />
    </div>
  </div>
);

const Words: React.FC<{ t: string; size: number; accent: string }> = ({ t, size, accent }) => {
  const parts = t.split("*");
  return <div style={{ color: "#fff", fontWeight: 900, fontSize: size, lineHeight: 1.0, letterSpacing: -2, textTransform: "uppercase", textShadow: "0 10px 30px rgba(0,0,0,0.8)" }}>
    {parts.map((p, i) => i % 2 ? <span key={i} style={{ color: accent }}>{p}</span> : <span key={i}>{p}</span>)}
  </div>;
};

export const Thumb3: React.FC<P> = (p) => {
  const acc = p.accent ?? C.yellow;
  const W = p.wide ? 1920 : 1080;
  const glow = <div style={{ position: "absolute", left: p.wide ? 900 : 140, top: p.wide ? 120 : 560, width: 800, height: 800, borderRadius: "50%", background: acc, filter: "blur(200px)", opacity: 0.35 }} />;
  const objW = p.wide ? 760 : 880;
  const obj = p.object === "card" ? <div style={{ transform: "rotate(-10deg)" }}><Card w={objW} label={p.label} /></div>
    : p.object === "toggle" ? <div style={{ position: "relative", transform: "rotate(-4deg)" }}><Toggle w={objW} label={p.label} on={p.on} /><div style={{ position: "absolute", right: -30, top: "50%", marginTop: -110, width: 300, height: 220, borderRadius: "50%", border: "12px solid #FF2D55" }} /></div>
    : p.object === "big" ? <div style={{ color: acc, fontWeight: 900, fontSize: Math.min(p.wide ? 420 : 380, Math.floor((p.wide ? 1500 : 1400) / Math.max(1, (p.big ?? "").length))), lineHeight: 0.9, letterSpacing: -10, whiteSpace: "nowrap", textShadow: `0 0 80px ${acc}88` }}>{p.big}</div>
    : <div style={{ width: objW, height: objW * 0.66, borderRadius: 30, overflow: "hidden", border: "8px solid #fff", transform: "rotate(-4deg)", boxShadow: "0 50px 100px rgba(0,0,0,0.6)" }}>{p.shot && <Img src={staticFile(p.shot)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />}</div>;
  if (p.wide) return (
    <AbsoluteFill style={{ fontFamily: FONT, background: "#0B0A1C", overflow: "hidden" }}>
      <style>{fontCss}</style>{glow}
      <div style={{ position: "absolute", left: 80, top: 0, bottom: 120, width: 860, display: "flex", alignItems: "center" }}><Words t={p.text} size={165} accent={acc} /></div>
      <div style={{ position: "absolute", right: 70, top: 150 }}>{obj}</div>
      <div style={{ position: "absolute", right: 200, bottom: -230, transform: "rotate(6deg)", filter: "drop-shadow(0 40px 60px rgba(0,0,0,0.6))" }}><Bait size={620} mood={p.mood ?? "shock"} /></div>
      <div style={{ position: "absolute", left: 80, bottom: 60 }}><Wordmark size={56} /></div>
    </AbsoluteFill>
  );
  return (
    <AbsoluteFill style={{ fontFamily: FONT, background: "#0B0A1C", overflow: "hidden" }}>
      <style>{fontCss}</style>{glow}
      <div style={{ position: "absolute", top: 170, left: 60, right: 60, textAlign: "center" }}><Words t={p.text} size={190} accent={acc} /></div>
      <div style={{ position: "absolute", top: p.object === "big" ? 760 : 840, left: 0, right: 0, display: "flex", justifyContent: "center" }}>{obj}</div>
      <div style={{ position: "absolute", bottom: -110, right: -60, transform: "rotate(8deg)", filter: "drop-shadow(0 40px 60px rgba(0,0,0,0.6))" }}><Bait size={700} mood={p.mood ?? "shock"} /></div>
      <div style={{ position: "absolute", left: 60, bottom: 60 }}><Wordmark size={50} /></div>
    </AbsoluteFill>
  );
};
