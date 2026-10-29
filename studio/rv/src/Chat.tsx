import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, Easing } from "remotion";
import { Bait, Wordmark, C, FONT, Socials } from "./brand";
import { fontCss } from "./parts";

/* «Промпт → ВИДАВ» (29.10, з розбору референсу власника): друкується промпт → обмін репліками → флеш «ВИДАВ» →
   відповідь на весь екран → 2–3 реакції. Чорний фон + один акцент, одне питання вгорі на весь ролик, без субтитрів озвучки. */
export type ChatData = {
  total: number; accent?: string; question: string; model: string; hook?: string;
  prompt: string; promptFrom: number; promptTo: number;
  turns: { who: "me" | "ai"; text: string; at: number }[];
  reveal: number; answer: string;
  reactions: { text: string; from: number; to: number }[];
  outroFrom: number; mouth: number[];
};

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const sp = (f: number, d = 12) => spring({ frame: f, fps: 30, config: { damping: d, mass: 0.7 } });
const typed = (text: string, f: number, from: number, to: number) => text.slice(0, Math.round(interpolate(f, [from, to], [0, text.length], clamp)));

const Bubble: React.FC<{ who: "me" | "ai"; text: string; k: number; accent: string; model: string }> = ({ who, text, k, accent, model }) => (
  <div style={{ alignSelf: who === "me" ? "flex-end" : "flex-start", maxWidth: 760, scale: `${k}`, opacity: k, transformOrigin: who === "me" ? "right bottom" : "left bottom" }}>
    {who === "ai" && <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 26, color: accent, marginBottom: 8, letterSpacing: 1 }}>{model}</div>}
    <div style={{ padding: "22px 30px", borderRadius: 30, fontFamily: FONT, fontWeight: 700, fontSize: 46, lineHeight: 1.2,
      background: who === "me" ? accent : "#1C1C22", color: who === "me" ? "#0B0A1C" : "white", border: who === "ai" ? "2px solid #2E2E38" : "none" }}>{text}</div>
  </div>
);

export const Chat: React.FC<ChatData> = (p) => {
  const f = useCurrentFrame();
  const A = p.accent ?? C.yellow;
  const preReveal = f < p.reveal;
  // камера: повільний наїзд на чат, удар на «ВИДАВ», далі — дрейф по відповіді
  const push = interpolate(f, [0, p.reveal], [1, 1.08], clamp);
  const kick = f >= p.reveal ? Math.exp(-(f - p.reveal) / 6) : 0;
  const flash = f >= p.reveal ? Math.max(0, 1 - (f - p.reveal) / 9) : 0;
  const ansK = sp(f - p.reveal - 6, 10);
  const inOutro = f >= p.outroFrom;
  const hl = (t: string) => t.split(/(\*[^*]+\*)/g).filter(Boolean).map((x, i) => x.startsWith("*") ? <span key={i} style={{ color: A }}>{x.slice(1, -1)}</span> : <span key={i}>{x}</span>);
  return (
    <AbsoluteFill style={{ background: "#07070A", fontFamily: FONT }}>
      <style>{fontCss}</style>
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 60%, ${A}22, transparent 60%)` }} />

      {!inOutro && (preReveal ? (
        /* --- 1. екран чату: промпт друкується, далі репліки --- */
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", scale: `${push}` }}>
          {p.hook && <div style={{ width: 980, textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 92, lineHeight: 1.05, color: "white", marginBottom: 40, letterSpacing: -1,
            textShadow: "0 8px 30px rgba(0,0,0,0.8)" }}>{hl(p.hook)}</div>}
          <div style={{ width: 960, padding: "40px 40px 30px", borderRadius: 44, background: "#111116", border: "2px solid #26262E", display: "flex", flexDirection: "column", gap: 22, marginTop: p.hook ? 0 : 120 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: FONT, fontWeight: 800, fontSize: 30, color: "#9A9AA8" }}>
              <div style={{ width: 18, height: 18, borderRadius: 9, background: A }} />{p.model}
            </div>
            {<div style={{ alignSelf: "flex-end", maxWidth: 860, padding: "24px 30px", borderRadius: 30, background: "#1C1C22", border: `2px solid ${A}66`,
              fontFamily: FONT, fontWeight: 700, fontSize: 36, lineHeight: 1.3, color: "white" }}>
              {typed(p.prompt, f, p.promptFrom, p.promptTo)}<span style={{ opacity: f < p.promptTo && Math.floor(f / 8) % 2 ? 1 : 0, color: A }}>|</span>
            </div>}
            {p.turns.filter((t) => f >= t.at).map((t, i) => <Bubble key={i} who={t.who} text={t.text} k={sp(f - t.at, 11)} accent={A} model={p.model} />)}
          </div>
        </AbsoluteFill>
      ) : (
        /* --- 2. ВИДАВ: відповідь на весь екран + реакції --- */
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", scale: `${1 + 0.12 * kick + 0.03 * ((f - p.reveal) / 120)}`, rotate: `${-2.5 * kick}deg` }}>
          <div style={{ position: "absolute", top: 360, fontFamily: FONT, fontWeight: 900, fontSize: 130, color: A, letterSpacing: -2, scale: `${sp(f - p.reveal, 8)}`,
            textShadow: `0 0 60px ${A}` }}>ВИДАВ.</div>
          <div style={{ width: 940, marginTop: 160, padding: "44px 46px", borderRadius: 40, background: "#15151B", border: `4px solid ${A}`, boxShadow: `0 0 ${40 + 20 * Math.sin(f / 6)}px ${A}66`,
            fontFamily: FONT, fontWeight: 800, fontSize: 62, lineHeight: 1.18, color: "white", textAlign: "left", scale: `${ansK}`, opacity: ansK }}>
            <div style={{ fontWeight: 800, fontSize: 28, color: A, marginBottom: 16 }}>{p.model}</div>
            {typed(p.answer, f, p.reveal + 6, p.reveal + 6 + Math.min(45, p.answer.length))}
          </div>
          {p.reactions.filter((r) => f >= r.from && f < r.to).map((r, i) => {
            const k = sp(f - r.from, 9);
            return <div key={i} style={{ position: "absolute", bottom: 330, left: 70, right: 70, textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 70, color: "white",
              WebkitTextStroke: "12px #07070A", paintOrder: "stroke fill", scale: `${k}`, rotate: `${(1 - k) * -6}deg` }}>{hl(r.text)}</div>;
          })}
        </AbsoluteFill>
      ))}

      {/* одне питання на весь ролик (магніт коментарів) */}
      {!inOutro && <div style={{ position: "absolute", top: 150, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
        <div style={{ background: "white", color: "#0B0A1C", fontFamily: FONT, fontWeight: 800, fontSize: 52, padding: "16px 34px", borderRadius: 22 }}>{p.question}</div>
      </div>}
      {!inOutro && <div style={{ position: "absolute", bottom: 60, right: 40, opacity: 0.95 }}><Bait size={170} mouth={p.mouth[f] ?? 0} mood={f >= p.reveal ? "happy" : "talk"} /></div>}
      <AbsoluteFill style={{ background: "white", opacity: flash * 0.55, pointerEvents: "none" }} />

      {inOutro && (
        <AbsoluteFill style={{ alignItems: "center", paddingTop: 300, scale: `${sp(f - p.outroFrom, 12)}` }}>
          <Bait size={300} withBody mouth={p.mouth[f] ?? 0} mood="happy" />
          <div style={{ marginTop: 30 }}><Wordmark size={110} /></div>
          <div style={{ marginTop: 50, fontFamily: FONT, fontWeight: 800, fontSize: 48, color: "white", textAlign: "center", padding: "0 80px" }}>Промпт — у нашому Telegram</div>
          <div style={{ marginTop: 50 }}><Socials scale={0.85} t={f - p.outroFrom} /></div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
