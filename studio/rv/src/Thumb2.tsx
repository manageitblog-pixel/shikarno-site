import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { Bait, Wordmark, C, FONT } from "./brand";
import { fontCss } from "./parts";
import { Icon } from "./Generic";

// Заставки v2 (власник 14.11: «яскраві, захоплюючі і різні кожен раз»).
// variant: react | screen | equation | number. pal — яскравий фон, різний для кожного ролику.
const PALS: Record<string, [string, string, string]> = {
  fire: ["#FF3D2E", "#FF9F1C", "#fff"],   // тривога/гроші
  lime: ["#19C37D", "#0BA360", "#fff"],   // безкоштовно/вигода
  ocean: ["#1E6BFF", "#00C2FF", "#fff"],  // техно/Google
  sun: ["#FFD60A", "#FF9F1C", "#0E0B24"], // новина/Україна
  grape: ["#7C5CFF", "#FF4F8B", "#fff"],  // бренд
  night: ["#0B0A1C", "#3B1A5A", "#fff"],  // темний контраст
};
type P = { variant: "react" | "screen" | "equation" | "number"; pal?: string; headline: string; tag?: string;
  mood?: "talk" | "happy" | "judge" | "shock"; icon?: string; shot?: string; left?: string; right?: string; result?: string; big?: string; sub?: string };

const Head: React.FC<{ text: string; size: number; color: string; hi: string; stroke?: boolean }> = ({ text, size, color, hi, stroke = true }) => {
  const parts = text.split("*");
  return (
    <div style={{ color, fontWeight: 900, fontSize: size, lineHeight: 1.0, letterSpacing: -2, textTransform: "uppercase", textAlign: "center",
      WebkitTextStroke: stroke ? "4px rgba(0,0,0,0.85)" : undefined, paintOrder: "stroke fill", textShadow: "0 12px 0 rgba(0,0,0,0.35)" }}>
      {parts.map((p, i) => i % 2 ? <span key={i} style={{ background: hi, color: hi === "#FFD60A" ? "#0E0B24" : "#fff", padding: "0 18px", borderRadius: 18, WebkitTextStroke: "0", display: "inline-block", transform: "rotate(-2deg)" }}>{p}</span> : <span key={i}>{p}</span>)}
    </div>
  );
};

export const Thumb2: React.FC<P> = (p) => {
  const [a, b, fg] = PALS[p.pal ?? "grape"] ?? PALS.grape;
  const hi = p.pal === "sun" ? "#0E0B24" : C.yellow;
  const bg = `radial-gradient(circle at 30% 25%, ${b} 0%, ${a} 55%, ${a} 100%)`;
  const rays = (
    <div style={{ position: "absolute", inset: -400, background: `repeating-conic-gradient(from 0deg at 50% 60%, rgba(255,255,255,0.10) 0deg 8deg, transparent 8deg 22deg)` }} />
  );
  const tag = p.tag ? (
    <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
      <div style={{ background: "#0E0B24", color: "#fff", fontWeight: 900, fontSize: 54, padding: "10px 34px", borderRadius: 18, letterSpacing: 2, border: `5px solid ${C.yellow}` }}>{p.tag}</div>
    </div>
  ) : null;
  const mark = <div style={{ position: "absolute", bottom: 40, left: 50, opacity: 0.95 }}><Wordmark size={46} /></div>;

  if (p.variant === "react") return (
    <AbsoluteFill style={{ fontFamily: FONT, background: bg, overflow: "hidden" }}>
      <style>{fontCss}</style>{rays}{tag}
      <div style={{ position: "absolute", top: 200, left: 40, right: 40 }}><Head text={p.headline} size={170} color={fg} hi={hi} /></div>
      {p.icon && <div style={{ position: "absolute", top: 930, right: 70, width: 260, height: 260, borderRadius: 70, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", transform: "rotate(10deg)", boxShadow: "0 30px 60px rgba(0,0,0,0.35)" }}><Icon name={p.icon} size={170} color={a} /></div>}
      <div style={{ position: "absolute", bottom: -60, left: -40, transform: "rotate(-8deg)", filter: "drop-shadow(0 40px 60px rgba(0,0,0,0.5))" }}><Bait size={860} mood={p.mood ?? "shock"} /></div>
      {mark}
    </AbsoluteFill>
  );

  if (p.variant === "screen") return (
    <AbsoluteFill style={{ fontFamily: FONT, background: bg, overflow: "hidden" }}>
      <style>{fontCss}</style>{rays}{tag}
      <div style={{ position: "absolute", top: 190, left: 40, right: 40 }}><Head text={p.headline} size={150} color={fg} hi={hi} /></div>
      <div style={{ position: "absolute", top: 760, left: 70, width: 940, height: 640, borderRadius: 36, overflow: "hidden", transform: "rotate(-4deg)", border: "10px solid #fff", boxShadow: "0 40px 80px rgba(0,0,0,0.5)", background: "#fff" }}>
        {p.shot && <Img src={staticFile(p.shot)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />}
      </div>
      <div style={{ position: "absolute", top: 900, left: 230, width: 520, height: 230, borderRadius: "50%", border: "12px solid #FF2D55", transform: "rotate(-6deg)" }} />
      <div style={{ position: "absolute", bottom: 30, right: 20, transform: "rotate(8deg)", filter: "drop-shadow(0 30px 50px rgba(0,0,0,0.5))" }}><Bait size={430} mood={p.mood ?? "shock"} /></div>
      {mark}
    </AbsoluteFill>
  );

  if (p.variant === "equation") {
    const chip = (t: string, bgc: string, c: string) => <div style={{ background: bgc, color: c, fontWeight: 900, fontSize: 92, padding: "26px 40px", borderRadius: 34, boxShadow: "0 24px 50px rgba(0,0,0,0.35)", textAlign: "center", lineHeight: 1.0 }}>{t}</div>;
    return (
      <AbsoluteFill style={{ fontFamily: FONT, background: bg, overflow: "hidden" }}>
        <style>{fontCss}</style>{rays}{tag}
        <div style={{ position: "absolute", top: 210, left: 40, right: 40 }}><Head text={p.headline} size={140} color={fg} hi={hi} /></div>
        <div style={{ position: "absolute", top: 700, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
          {chip(p.left ?? "", "#fff", "#0E0B24")}
          <div style={{ color: fg, fontWeight: 900, fontSize: 140, lineHeight: 0.9, WebkitTextStroke: "4px rgba(0,0,0,0.8)" }}>+</div>
          {chip(p.right ?? "", "#0E0B24", "#fff")}
          <div style={{ color: fg, fontWeight: 900, fontSize: 140, lineHeight: 0.9, WebkitTextStroke: "4px rgba(0,0,0,0.8)" }}>=</div>
          {chip(p.result ?? "?", C.yellow, "#0E0B24")}
        </div>
        <div style={{ position: "absolute", bottom: -40, right: -60, transform: "rotate(10deg)", filter: "drop-shadow(0 30px 50px rgba(0,0,0,0.5))" }}><Bait size={480} mood={p.mood ?? "judge"} /></div>
        {mark}
      </AbsoluteFill>
    );
  }

  // number
  return (
    <AbsoluteFill style={{ fontFamily: FONT, background: bg, overflow: "hidden" }}>
      <style>{fontCss}</style>{rays}{tag}
      <div style={{ position: "absolute", top: 230, left: 0, right: 0, textAlign: "center", color: fg, fontWeight: 900, fontSize: Math.min(420, Math.floor(1450 / Math.max(1, (p.big ?? "").length))), lineHeight: 0.9, letterSpacing: -10, whiteSpace: "nowrap",
        WebkitTextStroke: "8px rgba(0,0,0,0.85)", paintOrder: "stroke fill", textShadow: "0 20px 0 rgba(0,0,0,0.35)" }}>{p.big}</div>
      {p.sub && <div style={{ position: "absolute", top: 600, left: 0, right: 0, display: "flex", justifyContent: "center" }}><div style={{ background: "#0E0B24", color: C.yellow, fontWeight: 900, fontSize: 80, padding: "12px 36px", borderRadius: 22, transform: "rotate(-3deg)" }}>{p.sub}</div></div>}
      <div style={{ position: "absolute", top: 780, left: 40, right: 40 }}><Head text={p.headline} size={120} color={fg} hi={hi} /></div>
      <div style={{ position: "absolute", bottom: -50, left: "50%", marginLeft: -300, filter: "drop-shadow(0 40px 60px rgba(0,0,0,0.5))" }}><Bait size={600} mood={p.mood ?? "shock"} /></div>
      {mark}
    </AbsoluteFill>
  );
};

// Довгі 1920×1080: текст ліворуч (3–5 слів), праворуч — Байт / скрін / цифра; kicker — серія.
type L = P & { kicker?: string };
export const LongThumb2: React.FC<L> = (p) => {
  const [a, b, fg] = PALS[p.pal ?? "grape"] ?? PALS.grape;
  const hi = p.pal === "sun" ? "#0E0B24" : C.yellow;
  const bg = `radial-gradient(circle at 70% 40%, ${b} 0%, ${a} 60%, ${a} 100%)`;
  const parts = p.headline.split("*");
  const head = (
    <div style={{ position: "absolute", left: 70, top: p.kicker ? 210 : 120, width: p.variant === "react" ? 1000 : 900, color: fg, fontWeight: 900, fontSize: p.variant === "react" ? 150 : 124, lineHeight: 0.98, letterSpacing: -3, textTransform: "uppercase",
      WebkitTextStroke: "5px rgba(0,0,0,0.85)", paintOrder: "stroke fill", textShadow: "0 14px 0 rgba(0,0,0,0.35)" }}>
      {parts.map((t, i) => i % 2 ? <span key={i} style={{ background: hi, color: hi === "#FFD60A" ? "#0E0B24" : "#fff", padding: "0 18px", borderRadius: 18, WebkitTextStroke: "0", display: "inline-block", transform: "rotate(-2deg)" }}>{t}</span> : <span key={i}>{t}</span>)}
    </div>
  );
  return (
    <AbsoluteFill style={{ fontFamily: FONT, background: bg, overflow: "hidden" }}>
      <style>{fontCss}</style>
      <div style={{ position: "absolute", inset: -600, background: `repeating-conic-gradient(from 0deg at 70% 50%, rgba(255,255,255,0.10) 0deg 8deg, transparent 8deg 22deg)` }} />
      {p.kicker && <div style={{ position: "absolute", left: 70, top: 70, background: "#0E0B24", color: "#fff", fontWeight: 900, fontSize: 60, padding: "10px 34px", borderRadius: 20, border: `5px solid ${C.yellow}` }}>{p.kicker}</div>}
      {head}
      {p.variant === "screen" && p.shot && (
        <div style={{ position: "absolute", right: 60, top: 170, width: 820, height: 560, borderRadius: 30, overflow: "hidden", transform: "rotate(4deg)", border: "10px solid #fff", boxShadow: "0 40px 80px rgba(0,0,0,0.5)", background: "#fff" }}>
          <Img src={staticFile(p.shot)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />
          <div style={{ position: "absolute", left: 120, top: 150, width: 520, height: 200, borderRadius: "50%", border: "12px solid #FF2D55", transform: "rotate(-5deg)" }} />
        </div>
      )}
      {p.variant === "number" && <div style={{ position: "absolute", right: 60, top: 170, width: 860, textAlign: "center", whiteSpace: "nowrap", color: C.yellow, fontWeight: 900, fontSize: Math.min(330, Math.floor(1350 / Math.max(1, (p.big ?? "").length))), lineHeight: 0.9, WebkitTextStroke: "8px #0E0B24", paintOrder: "stroke fill", textShadow: "0 18px 0 rgba(0,0,0,0.35)", transform: "rotate(-4deg)" }}>{p.big}</div>}
      {p.icon && p.variant !== "screen" && <div style={{ position: "absolute", right: 520, top: 110, width: 220, height: 220, borderRadius: 60, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", transform: "rotate(-10deg)", boxShadow: "0 30px 60px rgba(0,0,0,0.35)" }}><Icon name={p.icon} size={150} color={a} /></div>}
      <div style={{ position: "absolute", right: p.variant === "screen" ? 0 : 40, bottom: p.variant === "react" ? -120 : -60, transform: "rotate(-6deg)", filter: "drop-shadow(0 40px 60px rgba(0,0,0,0.5))" }}>
        <Bait size={p.variant === "react" ? 760 : p.variant === "number" ? 380 : 470} mood={p.mood ?? "shock"} />
      </div>
      <div style={{ position: "absolute", left: 70, bottom: 50 }}><Wordmark size={60} /></div>
    </AbsoluteFill>
  );
};
