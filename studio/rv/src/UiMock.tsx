/* Схема інтерфейсу (не реальний запис): кроки з довідки Anthropic, анімовані курсором. Плашка «СХЕМА ІНТЕРФЕЙСУ» завжди в кадрі. */
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, Easing } from "remotion";
import { C, FONT } from "./brand";
import { Cursor } from "./parts";

export type UiStep = { t: string; [k: string]: any };
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const sp = (f: number, d = 14) => spring({ frame: f, fps: 30, config: { damping: d, mass: 0.8 } });
const W = 1440, H = 766, INK = "#1f1d2b", MUTED = "#6b6880", LINE = "#e7e5ef", ACC = "#7C5CFF";
const T = (s: number, w = 600, c = INK): React.CSSProperties => ({ fontFamily: FONT, fontWeight: w, fontSize: s, color: c });

/* координати цілі курсора для кожного кроку (у системі вікна) */
const target = (st: UiStep): [number, number] => {
  switch (st.t) {
    case "menu": return [150, 150 + (st.pick ?? 0) * 64];
    case "connect": return [1080, 252];
    case "oauth": return [860, 560];
    case "plus": return [330, 470 - ((st.items?.length ?? 1) - 1 - (st.pick ?? 0)) * 60];
    case "picker": return [700, 300 + (st.pick ?? 0) * 72];
    case "chat": return [1260, 520];
    case "perm": return [900 + 170 * (st.rows?.[st.rows.length - 1]?.[1] ?? 1), 210 + 96 * ((st.rows?.length ?? 1) - 1)];
    case "toggle": return [1080, 215 + 80 * (st.pick ?? 0)];
    default: return [720, 400];
  }
};

const Sidebar: React.FC<{ items: string[]; pick: number; k: number; crumbs?: string }> = ({ items, pick, k, crumbs }) => (
  <div style={{ position: "absolute", inset: 0, display: "flex" }}>
    <div style={{ width: 340, background: "#f6f5fa", borderRight: `2px solid ${LINE}`, padding: "40px 22px" }}>
      <div style={{ ...T(20, 800, MUTED), letterSpacing: 2, marginBottom: 18 }}>{crumbs ?? "МЕНЮ"}</div>
      {items.map((it, i) => (
        <div key={i} style={{ height: 52, marginBottom: 12, borderRadius: 14, display: "flex", alignItems: "center", padding: "0 20px",
          background: i === pick ? `rgba(124,92,255,${0.18 * k})` : "transparent", border: i === pick ? `2px solid rgba(124,92,255,${k})` : "2px solid transparent", ...T(25, i === pick ? 800 : 600) }}>{it}</div>
      ))}
    </div>
    <div style={{ flex: 1, padding: 50 }}>
      <div style={{ ...T(38, 800) }}>{items[pick]}</div>
      {[0, 1, 2].map((i) => <div key={i} style={{ height: 22, width: 560 - i * 120, borderRadius: 11, background: LINE, marginTop: 26 }} />)}
    </div>
  </div>
);

const Step: React.FC<{ st: UiStep; f: number; hist?: UiStep[] }> = ({ st, f, hist = [] }) => {
  const k = sp(f - 18);
  if (st.t === "menu") return <Sidebar items={st.items} pick={st.pick ?? 0} k={k} crumbs={st.crumbs} />;
  if (st.t === "connect") {
    const done = f > 40;
    return (
      <div style={{ position: "absolute", inset: 0, padding: 60, background: "white" }}>
        <div style={{ ...T(20, 800, MUTED), letterSpacing: 2 }}>{st.crumbs ?? "CUSTOMIZE › CONNECTORS"}</div>
        {(st.list ?? [st.name]).map((n: string, i: number) => {
          const me = n === st.name;
          return (
            <div key={i} style={{ marginTop: 24, height: 96, borderRadius: 20, border: `2px solid ${me ? ACC : LINE}`, display: "flex", alignItems: "center", padding: "0 30px", gap: 24, background: me ? "rgba(124,92,255,0.06)" : "white" }}>
              <div style={{ width: 52, height: 52, borderRadius: 14, background: ["#4CAF50", "#EA4335", "#4285F4"][i % 3], opacity: 0.85 }} />
              <div style={{ flex: 1, ...T(30, 800) }}>{n}</div>
              {me ? <div style={{ padding: "12px 30px", borderRadius: 14, background: done ? GREENBG : ACC, color: done ? "#0b6b3f" : "white", ...T(26, 800, done ? "#0b6b3f" : "white"), transform: `scale(${f > 30 && f < 40 ? 0.94 : 1})` }}>{done ? "Connected ✓" : st.btn ?? "Connect"}</div>
                : <div style={{ ...T(24, 600, MUTED) }}>Connect</div>}
            </div>);
        })}
      </div>);
  }
  if (st.t === "oauth") return (
    <div style={{ position: "absolute", inset: 0, background: "rgba(20,18,40,0.55)", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 640, borderRadius: 26, background: "white", padding: 44, boxShadow: "0 30px 80px rgba(0,0,0,0.4)", scale: `${0.9 + 0.1 * sp(f)}` }}>
        <div style={{ ...T(32, 800) }}>Вхід через Google-акаунт</div>
        <div style={{ ...T(24, 500, MUTED), marginTop: 12 }}>{st.account ?? "твій акаунт"}</div>
        <div style={{ ...T(23, 600), marginTop: 26, lineHeight: 1.5 }}>{(st.perms ?? []).map((p: string, i: number) => <div key={i} style={{ opacity: sp(f - 8 - i * 6) }}>• {p}</div>)}</div>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 18, marginTop: 34 }}>
          <div style={{ padding: "12px 26px", ...T(24, 700, MUTED) }}>Скасувати</div>
          <div style={{ padding: "12px 30px", borderRadius: 14, background: f > 44 ? "#2e7d32" : "#1a73e8", ...T(24, 800, "white") }}>{f > 44 ? "Дозволено ✓" : "Дозволити"}</div>
        </div>
      </div>
    </div>);
  if (st.t === "plus") {
    const items: string[] = st.items ?? [];
    return (
      <div style={{ position: "absolute", inset: 0, background: "white" }}>
        <ChatBox text={st.draft ?? ""} f={f} />
        <div style={{ position: "absolute", left: 260, bottom: 150, width: 520, borderRadius: 20, background: "white", border: `2px solid ${LINE}`, boxShadow: "0 20px 50px rgba(0,0,0,0.15)", padding: 12, opacity: sp(f - 6), translate: `0 ${(1 - sp(f - 6)) * 20}px` }}>
          {items.map((it, i) => <div key={i} style={{ height: 52, marginBottom: 8, borderRadius: 12, display: "flex", alignItems: "center", padding: "0 18px", background: i === st.pick ? `rgba(124,92,255,${0.18 * k})` : "transparent", ...T(25, i === st.pick ? 800 : 600) }}>{it}</div>)}
        </div>
      </div>);
  }
  if (st.t === "picker") {
    const q: string = st.query ?? ""; const typed = q.slice(0, Math.floor(f * 0.8));
    return (
      <div style={{ position: "absolute", inset: 0, background: "rgba(20,18,40,0.45)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: 900, borderRadius: 26, background: "white", padding: 36 }}>
          <div style={{ ...T(28, 800) }}>{st.title ?? "Файли з Диска"}</div>
          <div style={{ marginTop: 18, height: 60, borderRadius: 14, border: `2px solid ${ACC}`, display: "flex", alignItems: "center", padding: "0 20px", ...T(25, 600) }}>🔍 {typed}{typed.length < q.length ? "▌" : ""}</div>
          {(st.files ?? []).map((fl: string, i: number) => (
            <div key={i} style={{ marginTop: 12, height: 60, borderRadius: 14, display: "flex", alignItems: "center", padding: "0 20px", gap: 16, background: i === st.pick && f > 30 ? "rgba(124,92,255,0.14)" : "#f6f5fa", opacity: f > q.length / 0.8 ? 1 : 0.35, ...T(24, i === st.pick ? 800 : 600) }}>📄 {fl}</div>))}
        </div>
      </div>);
  }
  if (st.t === "chat") {
    const r: string = st.reply ?? ""; const shown = r.slice(0, Math.max(0, Math.floor((f - 24) * 3.2)));
    return (
      <div style={{ position: "absolute", inset: 0, background: "white", padding: "40px 120px", display: "flex", flexDirection: "column", justifyContent: "flex-end", paddingBottom: 70 }}>
        {hist.map((h, i) => <div key={i} style={{ opacity: 0.55, marginBottom: 22 }}>
          <div style={{ marginLeft: "auto", maxWidth: 900, width: "fit-content", padding: "14px 22px", borderRadius: 20, background: "#efeefe", ...T(23, 600) }}>{h.user}</div>
          <div style={{ marginTop: 12, maxWidth: 1100, ...T(22, 500), lineHeight: 1.45, whiteSpace: "pre-wrap" }}>{h.reply}</div></div>)}
        {st.file ? <div style={{ marginLeft: "auto", width: "fit-content", padding: "10px 18px", borderRadius: 14, background: "#f1effa", ...T(22, 700), marginBottom: 10 }}>📄 {st.file}</div> : null}
        <div style={{ marginLeft: "auto", maxWidth: 900, width: "fit-content", padding: "18px 26px", borderRadius: 24, background: "#efeefe", ...T(27, 600), opacity: sp(f) }}>{st.user}</div>
        {f > 20 ? <div style={{ marginTop: 26, maxWidth: 1100, ...T(26, 500), lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
          {st.tool && f > 14 ? <div style={{ ...T(20, 700, MUTED), marginBottom: 10 }}>⚙ {st.tool}</div> : null}{shown}</div> : null}
        {st.confirm && f > 24 + r.length / 3.2 + 6 ? <div style={{ marginTop: 18, display: "flex", gap: 16, opacity: sp(f - 24 - r.length / 3.2 - 6) }}>
          <div style={{ padding: "12px 26px", borderRadius: 14, background: ACC, ...T(24, 800, "white") }}>{st.confirm}</div>
          <div style={{ padding: "12px 26px", borderRadius: 14, border: `2px solid ${LINE}`, ...T(24, 700, MUTED) }}>Скасувати</div></div> : null}
      </div>);
  }
  if (st.t === "perm") {
    const rows: [string, number][] = st.rows ?? []; const modes = ["Always allow", "Needs approval", "Blocked"]; const col = ["#2e7d32", "#b26a00", "#c62828"];
    return (
      <div style={{ position: "absolute", inset: 0, background: "white", padding: "40px 60px" }}>
        <div style={{ ...T(20, 800, MUTED), letterSpacing: 2 }}>{st.crumbs ?? "CONNECTORS › TOOL PERMISSIONS"}</div>
        {rows.map(([name, m], i) => {
          const on = i < rows.length - 1 || f > 20;
          return (
            <div key={i} style={{ marginTop: 22, height: 74, display: "flex", alignItems: "center", gap: 20, borderBottom: `2px solid ${LINE}` }}>
              <div style={{ flex: 1, ...T(27, 700) }}>{name}</div>
              {modes.map((md, j) => <div key={j} style={{ width: 160, height: 50, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center",
                background: on && j === m ? col[j] : "#f3f2f8", ...T(17, 800, on && j === m ? "white" : MUTED) }}>{md}</div>)}
            </div>);
        })}
      </div>);
  }
  if (st.t === "toggle") {
    const items: [string, boolean][] = st.items ?? [];
    return (
      <div style={{ position: "absolute", inset: 0, background: "white" }}>
        <ChatBox text={st.draft ?? ""} f={f} />
        <div style={{ position: "absolute", left: 260, top: 150, width: 900, borderRadius: 20, border: `2px solid ${LINE}`, boxShadow: "0 20px 50px rgba(0,0,0,0.15)", padding: "16px 28px", background: "white" }}>
          <div style={{ ...T(22, 800, MUTED), letterSpacing: 2, marginBottom: 8 }}>«+» › CONNECTORS</div>
          {items.map(([n, v], i) => { const val = i === st.pick && f > 30 ? !v : v; return (
            <div key={i} style={{ height: 72, display: "flex", alignItems: "center", ...T(26, 700) }}><div style={{ flex: 1 }}>{n}</div>
              <div style={{ width: 76, height: 40, borderRadius: 20, background: val ? ACC : "#cfcde0", position: "relative" }}><div style={{ position: "absolute", top: 4, left: val ? 40 : 4, width: 32, height: 32, borderRadius: 16, background: "white" }} /></div></div>); })}
        </div>
      </div>);
  }
  return null;
};
const GREENBG = "#d7f5e5";

const ChatBox: React.FC<{ text: string; f: number }> = ({ text, f }) => (
  <div style={{ position: "absolute", left: 220, right: 220, bottom: 60, height: 84, borderRadius: 24, border: `2px solid ${LINE}`, display: "flex", alignItems: "center", gap: 20, padding: "0 24px", background: "white", boxShadow: "0 10px 30px rgba(0,0,0,0.08)" }}>
    <div style={{ width: 50, height: 50, borderRadius: 25, border: `2px solid ${LINE}`, display: "flex", alignItems: "center", justifyContent: "center", ...T(34, 600, MUTED) }}>+</div>
    <div style={{ ...T(25, 500, text ? INK : MUTED) }}>{text || "Напиши повідомлення…"}</div>
  </div>
);

export const UiMock: React.FC<{ title?: string; steps: UiStep[]; at: number[]; dur: number; src?: string }> = ({ title, steps, at, dur, src }) => {
  const f = useCurrentFrame(); const head = sp(f, 12);
  const starts = steps.map((_, i) => at[i] ?? Math.round((i * dur) / steps.length));
  let cur = 0; starts.forEach((s, i) => { if (f >= s) cur = i; });
  const lf = f - starts[cur];
  const [tx, ty] = target(steps[cur]); const [px, py] = cur > 0 ? target(steps[cur - 1]) : [W / 2, H - 60];
  const m = interpolate(lf, [2, 22], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const cx = px + (tx - px) * m, cy = py + (ty - py) * m;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 200, top: 130, display: "flex", alignItems: "center", gap: 18, opacity: head }}>
        <div style={{ padding: "8px 20px", borderRadius: 14, background: C.cyan, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 28, letterSpacing: 2 }}>СХЕМА ІНТЕРФЕЙСУ</div>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 44, color: "white" }}>{title}</div>
      </div>
      <div style={{ position: "absolute", left: 200, top: 196, width: W, height: H, borderRadius: 20, overflow: "hidden", background: "white", boxShadow: "0 40px 90px rgba(0,0,0,0.55)", border: "2px solid rgba(255,255,255,0.14)", opacity: head }}>
        <Step key={cur} st={steps[cur]} f={lf} hist={steps[cur].t === "chat" ? steps.slice(Math.max(0, cur - 2), cur).filter((x) => x.t === "chat" && !x.file) : []} />
        <div style={{ position: "absolute", right: 18, bottom: 14, padding: "6px 14px", borderRadius: 10, background: "rgba(14,11,36,0.75)", ...T(18, 700, "white") }}>{src ?? "кроки — за довідкою Anthropic · спрощена схема"}</div>
        <Cursor x={cx - 10} y={cy - 6} pressed={lf > 24 && lf < 32} />
      </div>
      <div style={{ position: "absolute", left: 200, top: 980, display: "flex", gap: 10 }}>
        {steps.map((_, i) => <div key={i} style={{ width: 46, height: 8, borderRadius: 4, background: i <= cur ? C.yellow : "rgba(255,255,255,0.2)" }} />)}
      </div>
    </AbsoluteFill>
  );
};
