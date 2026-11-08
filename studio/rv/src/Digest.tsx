import React, { createContext, useContext } from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, Easing, Img, staticFile, OffthreadVideo } from "remotion";
import { Bait, Wordmark, Avatar, C, FONT } from "./brand";
import { Cursor, fontCss } from "./parts";
import { Icon } from "./Generic";

export type DSeg = { kind: string; from: number; to: number; n?: number; icon?: string; title?: string; source?: string;
  points?: string[]; items?: any[]; score?: number; plus?: string; minus?: string; label?: string; at?: number[]; sub?: string;
  image?: string; hl?: { x: number; y: number; w: number; h: number }; url?: string; left?: { title: string; items: string[] }; right?: { title: string; items: string[] }; video?: string; vstart?: number; term?: { cmd: string; out: string; error?: boolean }[]; link?: string; zoom?: number[] };
export type DData = { total: number; num: number; dates: string; segs: DSeg[]; words: { w: string; s: number; e: number; g: string }[]; mouth: number[]; titles: string[]; kicker?: string; sub?: string; big?: string; agendaTitle?: string; red?: boolean };
const Ctx = createContext<DData>({ total: 300, num: 1, dates: "", segs: [], words: [], mouth: [], titles: [] });
const useD = () => useContext(Ctx);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const sp = (f: number, d = 12) => spring({ frame: f, fps: 30, config: { damping: d, mass: 0.8 } });
const GREEN = "#19C37D";

/* фон 16:9 */
const BG: React.FC = () => {
  const f = useCurrentFrame(); const a = f / 30;
  const blob = (x: number, y: number, s: number, c: string) => <div style={{ position: "absolute", left: x - s / 2, top: y - s / 2, width: s, height: s, borderRadius: "50%", background: c, filter: "blur(140px)", opacity: 0.5 }} />;
  return (
    <AbsoluteFill style={{ background: "linear-gradient(135deg,#0B0A1C 0%,#140F33 55%,#1A1240 100%)" }}>
      {blob(500 + Math.cos(a * 0.4) * 300, 400 + Math.sin(a * 0.6) * 150, 800, C.purple)}
      {blob(1450 + Math.sin(a * 0.35) * 300, 650 + Math.cos(a * 0.5) * 150, 700, C.pink)}
      {blob(960 + Math.cos(a * 0.3 + 2) * 400, 540, 500, "#00A3FF")}
      <AbsoluteFill style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.04) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.04) 2px, transparent 2px)", backgroundSize: "96px 96px", backgroundPosition: `${(f * 0.8) % 96}px 0`, maskImage: "radial-gradient(ellipse at center, black 35%, transparent 80%)" }} />
    </AbsoluteFill>
  );
};

/* шапка: бренд + номер випуску */
const Header: React.FC = () => {
  const { num, dates, kicker, red } = useD();
  return (
    <div style={{ position: "absolute", top: 36, left: 48, display: "flex", alignItems: "center", gap: 22 }}>
      <Avatar size={78} /><Wordmark size={48} />
      <div style={{ marginLeft: 10, padding: "10px 22px", borderRadius: 30, background: "rgba(255,255,255,0.1)", border: "2px solid rgba(255,255,255,0.25)", fontFamily: FONT, fontWeight: 800, fontSize: 28, color: "white", ...(red ? { background: "#FF2D55", border: "2px solid #FF2D55", boxShadow: "0 0 30px rgba(255,45,85,0.6)" } : {}) }}>
        {kicker ? `${kicker} · ${dates}` : `ДАЙДЖЕСТ #${num} · ${dates}`}
      </div>
    </div>
  );
};

/* розділи внизу */
const Chapters: React.FC = () => {
  const f = useCurrentFrame(); const { segs, total, titles } = useD();
  const starts = segs.filter((s) => s.kind === "points").map((s) => s.from);
  const cur = starts.filter((s) => f >= s).length;
  return (
    <div style={{ position: "absolute", left: 48, right: 48, bottom: 26, display: "flex", gap: 10, alignItems: "flex-end" }}>
      {titles.map((t, i) => {
        const active = cur === i + 1;
        return (
          <div key={i} style={{ flex: 1 }}>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 20, color: active ? C.yellow : "rgba(255,255,255,0.45)", marginBottom: 6, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{i + 1}. {t}</div>
            <div style={{ height: 8, borderRadius: 4, background: active ? C.yellow : cur > i + 1 ? "rgba(255,214,10,0.45)" : "rgba(255,255,255,0.15)" }} />
          </div>
        );
      })}
      <div style={{ width: 120, textAlign: "right", fontFamily: FONT, fontWeight: 700, fontSize: 22, color: "rgba(255,255,255,0.5)" }}>{Math.floor(f / 30 / 60)}:{String(Math.floor(f / 30) % 60).padStart(2, "0")}</div>
      <div style={{ position: "absolute", left: 0, top: -14, height: 4, width: `${(f / total) * 100}%`, background: "rgba(255,255,255,0.25)", borderRadius: 2 }} />
    </div>
  );
};

/* субтитри */
const Captions: React.FC = () => {
  const f = useCurrentFrame(); const { words: W } = useD();
  const cur = W.find((w) => f >= w.s && f < w.e) ?? [...W].reverse().find((w) => f >= w.e && f < w.e + 8);
  if (!cur) return null;
  const group = W.filter((w) => w.g === cur.g);
  return (
    <div style={{ position: "absolute", bottom: 108, left: 300, right: 300, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 18px" }}>
      {group.map((w, i) => {
        const a = f >= w.s && f < w.e;
        return <span key={i} style={{ fontFamily: FONT, fontWeight: 900, fontSize: 52, color: a ? C.yellow : "white", WebkitTextStroke: "10px black", paintOrder: "stroke fill" }}>{w.w}</span>;
      })}
    </div>
  );
};

/* ведучий */
const Host: React.FC<{ size?: number; x: number; y: number; mood?: any; offset: number }> = ({ size = 280, x, y, mood = "talk", offset }) => {
  const f = useCurrentFrame(); const { mouth } = useD();
  const k = sp(f, 11);
  return <div style={{ position: "absolute", left: x, top: y, scale: `${k}`, filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.5))" }}><Bait size={size} mouth={mouth[f + offset] ?? 0} mood={mood} /></div>;
};

const Intro: React.FC<{ off: number }> = ({ off }) => {
  const f = useCurrentFrame(); const { num, dates, kicker, sub, big, red } = useD();
  const t = sp(f - 6, 10), n = sp(f - 16, 8);
  const rays = interpolate(f, [0, 30], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: (1 - rays) * 0.8 }}>
        {Array.from({ length: 16 }).map((_, i) => <div key={i} style={{ position: "absolute", width: 14, height: 400 + rays * 1400, background: i % 2 ? C.yellow : C.pink, rotate: `${i * 22.5}deg`, borderRadius: 7, opacity: 0.6 }} />)}
      </AbsoluteFill>
      <Host size={420} x={230} y={260} mood="happy" offset={off} />
      <div style={{ position: "absolute", left: 820, top: 300, display: "flex", flexDirection: "column", gap: 26 }}>
        <div style={{ alignSelf: "flex-start", background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 40, padding: "10px 28px", borderRadius: 14, letterSpacing: 4, scale: `${t}`, ...(red ? { background: "#FF2D55", color: "white", boxShadow: "0 0 40px rgba(255,45,85,0.7)" } : {}) }}>{kicker ?? "ДАЙДЖЕСТ"}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 30, scale: `${n}`, transformOrigin: "left center" }}>
          {!big && <Wordmark size={150} />}
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: big ? 150 : 170, color: C.yellow, textShadow: "0 0 60px rgba(255,214,10,0.5)" }}>{big ?? `#${num}`}</span>
        </div>
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 52, color: "white", opacity: t }}>{sub ?? `Головне за тиждень · ${dates}`}</div>
      </div>
    </AbsoluteFill>
  );
};

const Agenda: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const items = (s.items ?? []) as [string, string][]; const { agendaTitle } = useD();
  const step = (dur - 40) / Math.max(1, items.length);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 140, top: 170, fontFamily: FONT, fontWeight: 900, fontSize: 64, color: "white", opacity: sp(f, 12) }}>{agendaTitle ?? "Сьогодні в дайджесті"}</div>
      <div style={{ position: "absolute", left: 140, top: 290, display: "flex", flexDirection: "column", gap: 22 }}>
        {items.map(([ic, tx], i) => {
          const a = s.at ? s.at[i] : 10 + i * step; const nx = s.at ? (i + 1 < s.at.length ? s.at[i + 1] : dur) : a + step; const k = sp(f - a, 11); const active = f >= a && f < nx;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 28, translate: `${(1 - k) * -300}px 0`, opacity: k }}>
              <div style={{ width: 70, fontFamily: FONT, fontWeight: 900, fontSize: 54, color: active ? C.yellow : "rgba(255,255,255,0.5)" }}>{i + 1}</div>
              <div style={{ width: 92, height: 92, borderRadius: 24, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center", scale: active ? "1.1" : "1" }}><Icon name={ic} size={58} /></div>
              <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 52, color: active ? "white" : "rgba(255,255,255,0.75)" }}>{tx}</div>
            </div>
          );
        })}
      </div>
      <Host size={300} x={1480} y={420} offset={off} />
    </AbsoluteFill>
  );
};

const Points: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const pts = s.points ?? [];
  const head = sp(f, 11); const step = (dur * 0.85) / Math.max(1, pts.length);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 110, top: 200, display: "flex", flexDirection: "column", alignItems: "center", gap: 30, scale: `${head}` }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 160, color: C.yellow, lineHeight: 1, textShadow: "0 0 50px rgba(255,214,10,0.45)" }}>{String(s.n).padStart(2, "0")}</div>
        <div style={{ width: 300, height: 300, borderRadius: 70, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 30px 70px rgba(124,92,255,0.5)", translate: `0 ${Math.sin(f / 12) * 8}px` }}>
          <Icon name={s.icon ?? "bolt"} size={190} />
        </div>
      </div>
      <div style={{ position: "absolute", left: 530, top: 190, right: 380 }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 68, color: "white", lineHeight: 1.1, opacity: head, translate: `0 ${(1 - head) * 30}px` }}>{s.title}</div>
        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 20 }}>
          {pts.map((p, i) => {
            const a = s.at ? s.at[i] : 12 + i * step; const nx = s.at ? (i + 1 < s.at.length ? s.at[i + 1] : dur) : a + step; const k = sp(f - a, 12); const active = f >= a && f < nx;
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 20, padding: "16px 26px", borderRadius: 24, background: active ? "rgba(255,214,10,0.14)" : "rgba(255,255,255,0.07)", border: `3px solid ${active ? C.yellow : "rgba(255,255,255,0.15)"}`, opacity: k, translate: `${(1 - k) * 200}px 0` }}>
                <Icon name="check" size={40} color={active ? C.yellow : GREEN} />
                <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 40, color: "white" }}>{p}</span>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 28, fontFamily: FONT, fontWeight: 600, fontSize: 26, color: "rgba(255,255,255,0.5)", opacity: interpolate(f, [30, 45], [0, 1], clamp) }}>Джерело: {s.source}</div>
      </div>
      <Host size={260} x={1560} y={470} offset={off} />
    </AbsoluteFill>
  );
};

/* скрін першоджерела / нашого тесту в рамці браузера: повільне наближення до підсвітки (рішення 5.11) */
const Evidence: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const head = sp(f, 12);
  const FW = 960, FH = 600; const IW = 1600, IH = 1000; const k0 = FW / IW;
  const hl = s.hl; const z = interpolate(f, [0, dur], [1, hl ? 1.35 : 1.06], { ...clamp, easing: Easing.inOut(Easing.quad) });
  const cx = hl ? (hl.x + hl.w / 2) * k0 : FW / 2, cy = hl ? (hl.y + hl.h / 2) * k0 : FH / 2;
  const hk = interpolate(f, [dur * 0.25, dur * 0.25 + 12], [0, 1], clamp);
  const demo = s.kind === "demo";
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 110, top: 150, display: "flex", alignItems: "center", gap: 18, opacity: head }}>
        <div style={{ padding: "8px 20px", borderRadius: 14, background: demo ? C.purple : C.yellow, color: demo ? "white" : C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 28, letterSpacing: 2 }}>{s.label ?? (demo ? "НАШ ТЕСТ" : "ДЖЕРЕЛО")}</div>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 46, color: "white" }}>{s.title}</div>
      </div>
      <div style={{ position: "absolute", left: 110, top: 220, width: FW, borderRadius: 22, overflow: "hidden", background: "#1d1b33", boxShadow: "0 40px 90px rgba(0,0,0,0.55)", border: "2px solid rgba(255,255,255,0.12)", opacity: head, translate: `0 ${(1 - head) * 40}px` }}>
        <div style={{ height: 52, display: "flex", alignItems: "center", gap: 10, padding: "0 20px", background: "rgba(255,255,255,0.06)" }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <div key={c} style={{ width: 16, height: 16, borderRadius: 8, background: c }} />)}
          <div style={{ marginLeft: 18, flex: 1, height: 32, borderRadius: 16, background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.7)", fontFamily: FONT, fontWeight: 600, fontSize: 20, display: "flex", alignItems: "center", padding: "0 18px", overflow: "hidden", whiteSpace: "nowrap" }}>{s.url ?? s.source}</div>
        </div>
        <div style={{ position: "relative", width: FW, height: FH, overflow: "hidden" }}>
          <div style={{ position: "absolute", left: 0, top: 0, width: FW, height: FH, transformOrigin: `${cx}px ${cy}px`, transform: `scale(${z})` }}>
            {s.image ? <Img src={staticFile(s.image)} style={{ width: FW, height: FH, objectFit: "cover", objectPosition: "top" }} /> : null}
            {hl ? <div style={{ position: "absolute", left: hl.x * k0 - 8, top: hl.y * k0 - 6, width: hl.w * k0 + 16, height: hl.h * k0 + 12, borderRadius: 10, border: `5px solid ${C.yellow}`, background: "rgba(255,214,10,0.16)", boxShadow: "0 0 40px rgba(255,214,10,0.55)", opacity: hk }} /> : null}
          </div>
        </div>
      </div>
      <Host size={240} x={1560} y={520} offset={off} />
    </AbsoluteFill>
  );
};


/* запис екрана реальної сторінки (rec.js): великий браузер, плашка з посиланням (рішення власника 8.11) */
const Screen: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const head = sp(f, 12);
  const W = 1440, H = 826;
  const z = s.zoom ? interpolate(f, [0, dur], [s.zoom[0], s.zoom[1]], { ...clamp, easing: Easing.inOut(Easing.quad) }) : interpolate(f, [0, dur], [1, 1.05], clamp);
  const lk = sp(f - 18, 14);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 200, top: 130, display: "flex", alignItems: "center", gap: 18, opacity: head }}>
        <div style={{ padding: "8px 20px", borderRadius: 14, background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 28, letterSpacing: 2 }}>{s.label ?? "ЕКРАН"}</div>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 44, color: "white" }}>{s.title}</div>
      </div>
      <div style={{ position: "absolute", left: 200, top: 196, width: W, borderRadius: 20, overflow: "hidden", background: "#1d1b33", boxShadow: "0 40px 90px rgba(0,0,0,0.55)", border: "2px solid rgba(255,255,255,0.14)", opacity: head, scale: `${0.96 + head * 0.04}` }}>
        <div style={{ height: 46, display: "flex", alignItems: "center", gap: 10, padding: "0 18px", background: "rgba(255,255,255,0.07)" }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <div key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />)}
          <div style={{ marginLeft: 16, flex: 1, height: 30, borderRadius: 15, background: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.8)", fontFamily: FONT, fontWeight: 600, fontSize: 19, display: "flex", alignItems: "center", padding: "0 16px", overflow: "hidden", whiteSpace: "nowrap" }}>🔒 {s.url}</div>
        </div>
        <div style={{ position: "relative", width: W, height: H - 46, overflow: "hidden", background: "white" }}>
          <div style={{ width: W, height: W * 1000 / 1600, transform: `scale(${z})`, transformOrigin: "50% 35%" }}>
            {s.video ? <OffthreadVideo src={staticFile(s.video)} startFrom={Math.round((s.vstart ?? 0) * 30)} muted style={{ width: W, height: W * 1000 / 1600 }} /> : null}
          </div>
        </div>
      </div>
      {s.link ? <div style={{ position: "absolute", left: 230, top: 965, padding: "12px 26px", borderRadius: 18, background: "rgba(11,10,28,0.92)", border: `3px solid ${C.cyan ?? "#4CF2FF"}`, fontFamily: FONT, fontWeight: 800, fontSize: 30, color: "white", opacity: lk, translate: `0 ${(1 - lk) * 30}px` }}>🔗 {s.link}</div> : null}
      <Host size={200} x={1640} y={720} offset={off} />
    </AbsoluteFill>
  );
};

/* термінал: команди друкуються, далі реальний вивід (лог реального запуску) */
const Terminal: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const head = sp(f, 12);
  const items = s.term ?? []; const n = Math.max(1, items.length); const slot = dur / n;
  const lines: React.ReactNode[] = [];
  items.forEach((it, i) => {
    const t0 = i * slot + 6; if (f < t0) return;
    const typed = Math.min(it.cmd.length, Math.floor((f - t0) * 2.2));
    const outAt = t0 + it.cmd.length / 2.2 + 10;
    lines.push(<div key={"c" + i} style={{ color: "#4CF2FF" }}><span style={{ color: "#19C37D" }}>shikarno@demo</span><span style={{ color: "white" }}>:~/nbu$ </span>{it.cmd.slice(0, typed)}{typed < it.cmd.length && Math.floor(f / 8) % 2 === 0 ? "▌" : ""}</div>);
    if (f >= outAt) { const shown = it.out.split("\n").slice(0, Math.floor((f - outAt) / 3) + 1);
      lines.push(<div key={"o" + i} style={{ color: it.error ? "#FF6B8B" : "rgba(255,255,255,0.88)", whiteSpace: "pre-wrap", marginBottom: 14 }}>{shown.join("\n")}</div>); }
  });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 200, top: 130, display: "flex", alignItems: "center", gap: 18, opacity: head }}>
        <div style={{ padding: "8px 20px", borderRadius: 14, background: C.purple, color: "white", fontFamily: FONT, fontWeight: 900, fontSize: 28, letterSpacing: 2 }}>{s.label ?? "ТЕРМІНАЛ · РЕАЛЬНИЙ ЗАПУСК"}</div>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 44, color: "white" }}>{s.title}</div>
      </div>
      <div style={{ position: "absolute", left: 200, top: 196, width: 1400, height: 760, borderRadius: 20, overflow: "hidden", background: "#0d0c17", boxShadow: "0 40px 90px rgba(0,0,0,0.6)", border: "2px solid rgba(255,255,255,0.14)", opacity: head }}>
        <div style={{ height: 44, display: "flex", alignItems: "center", gap: 10, padding: "0 18px", background: "rgba(255,255,255,0.07)" }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <div key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />)}
          <div style={{ marginLeft: 16, color: "rgba(255,255,255,0.6)", fontFamily: "monospace", fontSize: 20 }}>bash — Claude Code {""}</div>
        </div>
        <div style={{ padding: "22px 30px", fontFamily: "'DejaVu Sans Mono', monospace", fontSize: 25, lineHeight: 1.45, display: "flex", flexDirection: "column", justifyContent: "flex-end", height: 760 - 44 - 44, overflow: "hidden" }}>{lines}</div>
      </div>
      <Host size={200} x={1640} y={720} offset={off} />
    </AbsoluteFill>
  );
};

/* дві колонки: було/стало або ChatGPT vs Gemini */
const Compare: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const head = sp(f, 12);
  const col = (c: { title: string; items: string[] } | undefined, i: number, color: string) => {
    const k = sp(f - 8 - i * 10, 12);
    return (
      <div style={{ flex: 1, minWidth: 0, borderRadius: 30, padding: "34px 38px", background: "rgba(255,255,255,0.07)", border: `3px solid ${color}`, opacity: k, translate: `0 ${(1 - k) * 60}px` }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 52, color }}>{c?.title}</div>
        <div style={{ marginTop: 26, display: "flex", flexDirection: "column", gap: 18 }}>
          {(c?.items ?? []).map((t, j) => {
            const kk = sp(f - 20 - i * 10 - j * Math.max(6, dur * 0.12), 13);
            return <div key={j} style={{ fontFamily: FONT, fontWeight: 700, fontSize: 36, color: "white", opacity: kk, translate: `${(1 - kk) * 40}px 0` }}>• {t}</div>;
          })}
        </div>
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 110, top: 160, right: 400, fontFamily: FONT, fontWeight: 900, fontSize: 64, color: "white", opacity: head }}>{s.title}</div>
      <div style={{ position: "absolute", left: 110, top: 290, right: 400, display: "flex", gap: 36 }}>
        {col(s.left, 0, "rgba(255,255,255,0.55)")}
        {col(s.right, 1, C.yellow)}
      </div>
      <Host size={240} x={1580} y={520} offset={off} />
    </AbsoluteFill>
  );
};

const Verdict: React.FC<{ s: DSeg; off: number }> = ({ s, off }) => {
  const f = useCurrentFrame(); const sc = (s.score ?? 8) / 10;
  const p = interpolate(f, [6, 40], [0, sc], { ...clamp, easing: Easing.out(Easing.cubic) });
  const R = 170, Cc = 2 * Math.PI * R;
  const chip = (at: number, good: boolean, t?: string) => { const k = sp(f - at, 12);
    return <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "16px 28px", borderRadius: 22, scale: `${k}`, opacity: k, background: good ? "rgba(25,195,125,0.18)" : "rgba(255,79,139,0.18)", border: `3px solid ${good ? GREEN : C.pink}`, fontFamily: FONT, fontWeight: 800, fontSize: 40, color: "white" }}><span style={{ color: good ? GREEN : C.pink, fontSize: 50 }}>{good ? "+" : "−"}</span>{t}</div>; };
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 300, top: 220, width: 420, height: 420 }}>
        <svg width="420" height="420" viewBox="0 0 420 420" style={{ rotate: "-90deg" }}>
          <circle cx="210" cy="210" r={R} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="34" />
          <circle cx="210" cy="210" r={R} fill="none" stroke={C.yellow} strokeWidth="34" strokeLinecap="round" strokeDasharray={Cc} strokeDashoffset={Cc * (1 - p)} style={{ filter: `drop-shadow(0 0 16px ${C.yellow})` }} />
        </svg>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: FONT, color: "white" }}>
          <div style={{ fontWeight: 900, fontSize: 180, lineHeight: 1 }}>{Math.round(p * 10)}</div>
          <div style={{ fontWeight: 800, fontSize: 48, opacity: 0.7 }}>/ 10</div>
        </AbsoluteFill>
      </div>
      <div style={{ position: "absolute", left: 820, top: 250, display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={{ alignSelf: "flex-start", background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 36, padding: "8px 24px", borderRadius: 12, letterSpacing: 2 }}>{s.label ?? "ВЕРДИКТ БАЙТА"}</div>
        {chip(30, true, s.plus)}{chip(55, false, s.minus)}
      </div>
      <Host size={260} x={1560} y={470} mood="judge" offset={off} />
    </AbsoluteFill>
  );
};

const Quick: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const items = (s.items ?? []) as [string, string][];
  const step = (dur - 20) / Math.max(1, items.length);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 140, top: 180, background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 52, padding: "10px 34px", borderRadius: 16, letterSpacing: 4, scale: `${sp(f, 9)}` }}>КОРОТКО</div>
      <div style={{ position: "absolute", left: 140, top: 320, right: 420, display: "flex", flexDirection: "column", gap: 26 }}>
        {items.map(([ic, tx], i) => { const a = s.at ? s.at[i] : 6 + i * step; const nx = s.at ? (i + 1 < s.at.length ? s.at[i + 1] : dur) : a + step; const k = sp(f - a, 11); const active = f >= a && f < nx;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 26, padding: "22px 30px", borderRadius: 28, background: active ? "rgba(255,214,10,0.14)" : "rgba(255,255,255,0.07)", border: `3px solid ${active ? C.yellow : "rgba(255,255,255,0.15)"}`, opacity: k, translate: `0 ${(1 - k) * 60}px` }}>
              <div style={{ width: 84, height: 84, borderRadius: 22, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}><Icon name={ic} size={52} /></div>
              <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 40, color: "white" }}>{tx}</span>
            </div>
          ); })}
      </div>
      <Host size={280} x={1540} y={440} offset={off} />
    </AbsoluteFill>
  );
};

/* розділ (1.11): велика картка «Розділ N» між блоками довгих випусків */
const Section: React.FC<{ s: DSeg }> = ({ s }) => {
  const f = useCurrentFrame(); const k = sp(f, 10); const k2 = sp(f - 8, 12);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 60, scale: `${0.9 + 0.1 * k}`, opacity: k }}>
        <div style={{ width: 260, height: 260, borderRadius: 64, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 90px rgba(124,92,255,0.6)", rotate: `${(1 - k) * -25}deg` }}><Icon name={s.icon ?? "bolt"} size={160} /></div>
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ alignSelf: "flex-start", background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 44, padding: "8px 30px", borderRadius: 14, letterSpacing: 4 }}>РОЗДІЛ {s.n}</div>
          <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 104, color: "white", lineHeight: 1, opacity: k2, translate: `${(1 - k2) * 80}px 0` }}>{s.title}</div>
          {s.sub && <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 46, color: C.cyan, opacity: k2 }}>{s.sub}</div>}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* цифри / календар / хронологія: items [["значення","підпис"], ...] — по черзі, синхронно з реченнями (at) */
const Facts: React.FC<{ s: DSeg; dur: number; off: number }> = ({ s, dur, off }) => {
  const f = useCurrentFrame(); const items = (s.items ?? []) as [string, string][];
  const step = (dur - 20) / Math.max(1, items.length);
  const head = s.kind === "numbers" ? "ЦИФРИ" : s.kind === "calendar" ? "КАЛЕНДАР" : "ХРОНОЛОГІЯ";
  const big = items.length > 5;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 140, top: 150, background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 52, padding: "10px 34px", borderRadius: 16, letterSpacing: 4, scale: `${sp(f, 9)}` }}>{head}</div>
      <div style={{ position: "absolute", left: 140, top: 270, right: 420, display: "flex", flexDirection: "column", gap: big ? 16 : 24 }}>
        {items.map(([v, tx], i) => { const a = s.at ? s.at[i] : 6 + i * step; const nx = s.at ? (i + 1 < s.at.length ? s.at[i + 1] : dur) : a + step; const k = sp(f - a, 11); const active = f >= a && f < nx;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 30, padding: big ? "12px 26px" : "18px 30px", borderRadius: 26, background: active ? "rgba(255,214,10,0.14)" : "rgba(255,255,255,0.07)", border: `3px solid ${active ? C.yellow : "rgba(255,255,255,0.15)"}`, opacity: k, translate: `0 ${(1 - k) * 60}px` }}>
              {s.kind === "timeline"
                ? <div style={{ width: 84, height: 84, borderRadius: 22, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}><Icon name={v} size={52} /></div>
                : <div style={{ minWidth: 300, fontFamily: FONT, fontWeight: 900, fontSize: big ? 46 : 56, color: active ? C.yellow : C.cyan }}>{v}</div>}
              <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: big ? 34 : 40, color: "white" }}>{tx}</span>
            </div>
          ); })}
      </div>
      <Host size={280} x={1540} y={440} offset={off} />
    </AbsoluteFill>
  );
};

const Outro: React.FC<{ off: number }> = ({ off }) => {
  const f = useCurrentFrame();
  const tap = 150; const sub = f >= tap; const pressed = f >= tap && f < tap + 5;
  const cx = interpolate(f, [110, 145], [1500, 1180], { ...clamp, easing: Easing.out(Easing.cubic) });
  const cy = interpolate(f, [110, 145], [1000, 560], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill>
      <Host size={440} x={220} y={240} mood={sub ? "happy" : "talk"} offset={off} />
      <div style={{ position: "absolute", left: 820, top: 230, display: "flex", flexDirection: "column", gap: 34 }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 60, color: "white", opacity: sp(f, 12) }}>Яка новина тижня — твоя?</div>
        <div style={{ display: "flex", alignItems: "center", gap: 26, scale: `${sp(f - 20, 10) * (pressed ? 0.93 : 1)}`, transformOrigin: "left center" }}>
          <div style={{ padding: "26px 56px", borderRadius: 60, background: sub ? "#3A3A4A" : "#FF2D2D", color: "white", fontFamily: FONT, fontWeight: 900, fontSize: 50, boxShadow: sub ? "none" : "0 0 50px rgba(255,45,45,0.6)" }}>{sub ? "Ви підписані ✓" : "ПІДПИСАТИСЬ"}</div>
          <svg width="90" height="90" viewBox="0 0 24 24" style={{ rotate: `${sub ? Math.sin((f - tap) * 1.2) * 22 * Math.exp(-(f - tap) / 14) : 0}deg`, transformOrigin: "50% 10%" }}><path d="M12 2a6 6 0 0 0-6 6v4l-2 4h16l-2-4V8a6 6 0 0 0-6-6zm-2.5 16a2.5 2.5 0 0 0 5 0z" fill={sub ? C.yellow : "white"} /></svg>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "14px 30px", borderRadius: 40, background: "rgba(42,171,238,0.18)", border: "3px solid #2AABEE", alignSelf: "flex-start", opacity: interpolate(f, [50, 65], [0, 1], clamp) }}>
          <svg width="46" height="46" viewBox="0 0 24 24"><path d="M21 4L3 11l6 2 2 6 3-4 5 4z" fill="#2AABEE" /></svg>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 44, color: "white" }}>Telegram: @shikarno_ai_ua</span>
        </div>
      </div>
      <Cursor x={cx} y={cy} pressed={pressed} />
    </AbsoluteFill>
  );
};

export const DigestVideo: React.FC<DData> = (props) => {
  const S = props.segs;
  return (
    <Ctx.Provider value={props}>
      <AbsoluteFill style={{ fontFamily: FONT }}>
        <style>{fontCss}</style>
        <BG />
        {S.map((s, i) => {
          const start = i === 0 ? 0 : s.from - 6; const end = i < S.length - 1 ? S[i + 1].from - 6 : props.total; const dur = end - start;
          const out = (x: React.ReactNode) => <Sequence key={i} from={start} durationInFrames={dur}><Fade dur={dur}>{x}</Fade></Sequence>;
          if (s.kind === "intro") return out(<Intro off={start} />);
          if (s.kind === "agenda") return out(<Agenda s={s} dur={dur} off={start} />);
          if (s.kind === "points") return out(<Points s={s} dur={dur} off={start} />);
          if (s.kind === "verdict") return out(<Verdict s={s} off={start} />);
          if (s.kind === "evidence" || s.kind === "demo") return out(<Evidence s={s} dur={dur} off={start} />);
          if (s.kind === "compare") return out(<Compare s={s} dur={dur} off={start} />);
          if (s.kind === "screen") return out(<Screen s={s} dur={dur} off={start} />);
          if (s.kind === "terminal") return out(<Terminal s={s} dur={dur} off={start} />);
          if (s.kind === "quick") return out(<Quick s={s} dur={dur} off={start} />);
          if (s.kind === "section") return out(<Section s={s} />);
          if (s.kind === "numbers" || s.kind === "calendar" || s.kind === "timeline") return out(<Facts s={s} dur={dur} off={start} />);
          return out(<Outro off={start} />);
        })}
        <Header />
        <Captions />
        <Chapters />
      </AbsoluteFill>
    </Ctx.Provider>
  );
};

const Fade: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: interpolate(f, [0, 8, dur - 8, dur], [0, 1, 1, 0], clamp) }}>{children}</AbsoluteFill>;
};

export const DigestThumb: React.FC<{ num: number; dates: string; icons: string[]; headline: string; kicker?: string; red?: boolean }> = ({ num, dates, icons, headline, kicker, red }) => (
  <AbsoluteFill style={{ fontFamily: FONT, background: "linear-gradient(135deg,#0B0A1C 0%,#1A1240 60%,#3B1A5A 100%)" }}>
    <style>{fontCss}</style>
    <div style={{ position: "absolute", left: -120, top: -120, width: 700, height: 700, borderRadius: "50%", background: C.purple, filter: "blur(140px)", opacity: 0.6 }} />
    <div style={{ position: "absolute", right: -100, bottom: -160, width: 700, height: 700, borderRadius: "50%", background: C.pink, filter: "blur(140px)", opacity: 0.55 }} />
    <div style={{ position: "absolute", left: 70, top: 60, display: "flex", alignItems: "center", gap: 24 }}>
      <div style={{ background: red ? "#FF2D55" : C.yellow, color: red ? "white" : C.ink, fontWeight: 900, fontSize: 64, padding: "8px 30px", borderRadius: 18, boxShadow: red ? "0 0 50px rgba(255,45,85,0.7)" : undefined }}>{kicker ?? `ДАЙДЖЕСТ #${num}`}</div>
      <div style={{ color: "white", fontWeight: 800, fontSize: 40, opacity: 0.85 }}>{dates}</div>
    </div>
    <div style={{ position: "absolute", left: 70, top: 200, width: 1150, color: "white", fontWeight: 900, fontSize: 104, lineHeight: 1.05, textShadow: "0 8px 30px rgba(0,0,0,0.6)" }}>{headline}</div>
    <div style={{ position: "absolute", left: 70, bottom: 70, display: "flex", gap: 22 }}>
      {icons.map((ic, i) => (
        <div key={i} style={{ width: 130, height: 130, borderRadius: 34, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center", border: "4px solid rgba(255,255,255,0.3)" }}><Icon name={ic} size={84} /></div>
      ))}
    </div>
    <div style={{ position: "absolute", right: 40, bottom: 30, filter: "drop-shadow(0 30px 50px rgba(0,0,0,0.6))" }}><Bait size={520} mood="judge" /></div>
    <div style={{ position: "absolute", right: 60, top: 60 }}><Wordmark size={70} /></div>
  </AbsoluteFill>
);

// tone — колір рубрики (лад на сторінці каналу): free зелений · scam червоний · check бірюзовий · news жовтий · try фіолетовий
const TONES: Record<string, [string, string]> = { free: ["#19C37D", "#0B0A1C"], scam: ["#FF2D55", "#fff"], check: ["#4CF2FF", "#0B0A1C"], news: [C.yellow, C.ink], try: ["#7C5CFF", "#fff"] };
export const ShortThumb: React.FC<{ tag: string; red?: boolean; headline: string; icon: string; mood?: "talk" | "happy" | "judge"; tone?: string }> = ({ tag, red, headline, icon, mood = "happy", tone }) => {
  const parts = headline.split("*");
  if (tone && TONES[tone]) return <ToneThumb tag={tag} headline={headline} icon={icon} mood={mood} tone={tone} />;
  return (
    <AbsoluteFill style={{ fontFamily: FONT, background: "linear-gradient(160deg,#0B0A1C 0%,#1A1240 55%,#3B1A5A 100%)", alignItems: "center" }}>
      <style>{fontCss}</style>
      <div style={{ position: "absolute", left: -200, top: 200, width: 800, height: 800, borderRadius: "50%", background: C.purple, filter: "blur(160px)", opacity: 0.6 }} />
      <div style={{ position: "absolute", right: -200, bottom: 100, width: 800, height: 800, borderRadius: "50%", background: red ? "#FF2D55" : C.pink, filter: "blur(160px)", opacity: 0.5 }} />
      <div style={{ position: "absolute", top: 110 }}><Wordmark size={64} /></div>
      <div style={{ position: "absolute", top: 230, background: red ? "#FF2D55" : C.yellow, color: red ? "#fff" : C.ink, fontWeight: 900, fontSize: 58, padding: "12px 40px", borderRadius: 22, letterSpacing: 2, boxShadow: red ? "0 0 50px rgba(255,45,85,0.8)" : "0 16px 40px rgba(0,0,0,0.4)" }}>{tag}</div>
      <div style={{ position: "absolute", top: 400, width: 330, height: 330, borderRadius: 80, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center", border: "6px solid rgba(255,255,255,0.3)", boxShadow: "0 40px 90px rgba(124,92,255,0.6)" }}><Icon name={icon} size={200} /></div>
      <div style={{ position: "absolute", top: 790, width: 960, textAlign: "center", color: "white", fontWeight: 900, fontSize: 112, lineHeight: 1.06, textShadow: "0 10px 34px rgba(0,0,0,0.7)" }}>
        {parts.map((p, i) => i % 2 ? <span key={i} style={{ color: C.yellow }}>{p}</span> : <span key={i}>{p}</span>)}
      </div>
      <div style={{ position: "absolute", bottom: 90, filter: "drop-shadow(0 30px 50px rgba(0,0,0,0.6))" }}><Bait size={430} mood={mood} /></div>
    </AbsoluteFill>
  );
};

const ToneThumb: React.FC<{ tag: string; headline: string; icon: string; mood: "talk" | "happy" | "judge"; tone: string }> = ({ tag, headline, icon, mood, tone }) => {
  const [bg, fg] = TONES[tone]; const parts = headline.split("*");
  const len = headline.replace(/\*/g, "").length; const fs = len > 26 ? 122 : len > 18 ? 140 : 160;
  return (
    <AbsoluteFill style={{ fontFamily: FONT, background: "linear-gradient(160deg,#0B0A1C 0%,#140F33 60%,#22164A 100%)", alignItems: "center" }}>
      <style>{fontCss}</style>
      <div style={{ position: "absolute", left: -260, top: 380, width: 900, height: 900, borderRadius: "50%", background: bg, filter: "blur(220px)", opacity: 0.35 }} />
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 26, background: bg }} />
      <div style={{ position: "absolute", top: 120 }}><Wordmark size={60} /></div>
      <div style={{ position: "absolute", top: 250, background: bg, color: fg, fontWeight: 900, fontSize: 60, padding: "14px 44px", borderRadius: 24, letterSpacing: 1, boxShadow: `0 0 60px ${bg}88` }}>{tag}</div>
      <div style={{ position: "absolute", top: 400, bottom: 520, width: 1000, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", color: "white", fontWeight: 900, fontSize: fs, lineHeight: 1.04, letterSpacing: -1, textShadow: "0 10px 34px rgba(0,0,0,0.8)" }}>
        <div>{parts.map((p, i) => i % 2 ? <span key={i} style={{ color: bg }}>{p}</span> : <span key={i}>{p}</span>)}</div>
      </div>
      <div style={{ position: "absolute", bottom: 150, left: 90, width: 260, height: 260, borderRadius: 70, background: `${bg}22`, border: `6px solid ${bg}`, display: "flex", alignItems: "center", justifyContent: "center", rotate: "-8deg" }}><Icon name={icon} size={160} color={bg} /></div>
      <div style={{ position: "absolute", bottom: 70, right: 60, filter: "drop-shadow(0 30px 50px rgba(0,0,0,0.6))" }}><Bait size={380} mood={mood} /></div>
    </AbsoluteFill>
  );
};
