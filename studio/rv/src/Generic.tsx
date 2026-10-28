import React, { createContext, useContext } from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, Easing } from "remotion";
import { Highlight } from "@remotion/rough-notation";
import { Bait, Wordmark, Avatar, C, FONT, Socials } from "./brand";
import { Background, Cursor, fontCss } from "./parts";

/* ---------- дані епізоду (через inputProps) ---------- */
export type Scene = {
  kind: string; label: string; title: string; from: number; to: number;
  icon?: string; items?: any[]; before?: string; after?: string;
  big?: string; sub?: string; foot?: string; score?: number; plus?: string; minus?: string; badge?: string; hook?: string;
};
export type EpData = { total: number; scenes: Scene[]; words: { w: string; s: number; e: number; g: string }[]; mouth: number[]; alert?: string };
const Ctx = createContext<EpData>({ total: 300, scenes: [], words: [], mouth: [] });
const useEp = () => useContext(Ctx);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const sp = (f: number, damping = 12) => spring({ frame: f, fps: 30, config: { damping, mass: 0.8 } });
const INTRO = 26;
const GREEN = "#19C37D";

/* ---------- іконки ---------- */
export const Icon: React.FC<{ name: string; size?: number; color?: string }> = ({ name, size = 64, color = "white" }) => {
  const p = { fill: "none", stroke: color, strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const g: Record<string, React.ReactNode> = {
    browser: <><rect x="2" y="4" width="20" height="16" rx="3" {...p} /><path d="M2 9h20" {...p} /><circle cx="5.5" cy="6.5" r=".8" fill={color} /><circle cx="8" cy="6.5" r=".8" fill={color} /><path d="M12 13l3 6 1-2.5 2.5-1z" fill={color} stroke={color} strokeWidth="1" /></>,
    video: <><rect x="2" y="5" width="15" height="14" rx="3" {...p} /><path d="M17 10l5-3v10l-5-3z" {...p} /><path d="M8 9.5v5l4-2.5z" fill={color} /></>,
    form: <><rect x="4" y="2" width="16" height="20" rx="2" {...p} /><path d="M8 7h8M8 11h8M8 15h4" {...p} /><path d="M14 17l2 2 4-4" {...p} /></>,
    chat: <><path d="M4 4h16v11H9l-5 4z" {...p} /><path d="M8 9h8M8 12h5" {...p} /></>,
    download: <><path d="M12 3v12M7 10l5 5 5-5" {...p} /><path d="M4 19h16" {...p} /></>,
    text: <><path d="M4 6h16M4 11h16M4 16h10" {...p} /></>,
    image: <><rect x="3" y="4" width="18" height="16" rx="3" {...p} /><circle cx="9" cy="10" r="2" {...p} /><path d="M3 17l5-5 4 4 3-3 6 6" {...p} /></>,
    bolt: <path d="M13 2L4 14h7l-1 8 9-12h-7z" {...p} />,
    money: <><circle cx="12" cy="12" r="9" {...p} /><path d="M15 8.5c-.8-1-2-1.5-3-1.5-1.7 0-3 1-3 2.5S10.5 12 12 12s3 .8 3 2.5-1.3 2.5-3 2.5c-1.2 0-2.4-.5-3.2-1.5M12 5v2M12 17v2" {...p} /></>,
    check: <path d="M4 12.5l5 5L20 6.5" {...p} />,
    car: <><path d="M2 15.5v-3.5l3-1 3.5-4h7l4 4 2.5 1v3.5" {...p} /><path d="M8.5 11h11M12.5 7v4" {...p} /><path d="M9 15.5h6" {...p} /><circle cx="6.5" cy="16" r="2" {...p} /><circle cx="17.5" cy="16" r="2" {...p} /></>,
    mail: <><rect x="3" y="5" width="18" height="14" rx="2" {...p} /><path d="M3 7l9 6 9-6" {...p} /></>,
    map: <><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" {...p} /><circle cx="12" cy="9.5" r="2.5" {...p} /></>,
    warning: <><path d="M12 3l10 18H2z" {...p} /><path d="M12 10v5" {...p} /><circle cx="12" cy="18" r=".9" fill={color} /></>,
    shield: <><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" {...p} /><path d="M8.5 12l2.5 2.5 4.5-5" {...p} /></>,
    chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" {...p} /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24">{g[name] ?? g.bolt}</svg>;
};

/* ---------- верх: плашка бренду + прогрес ---------- */
const TopBrand: React.FC = () => {
  const f = useCurrentFrame(); const { total, alert } = useEp();
  const show = sp(f - INTRO + 4, 14);
  return (
    <>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 12, background: "rgba(255,255,255,0.12)" }}>
        <div style={{ width: `${(f / total) * 100}%`, height: "100%", background: C.yellow }} />
      </div>
      <div style={{
        position: "absolute", top: 92, left: "50%", translate: "-50% 0", scale: `${show}`, opacity: show,
        display: "flex", alignItems: "center", gap: 18, padding: "10px 30px 10px 12px", borderRadius: 60,
        background: "rgba(14,11,36,0.55)", border: "2px solid rgba(255,255,255,0.22)",
      }}>
        <Avatar size={72} /><Wordmark size={46} />
      </div>
      {alert && <div style={{
        position: "absolute", top: 196, left: "50%", translate: "-50% 0", scale: `${show}`, opacity: show * (0.82 + 0.18 * Math.sin(f / 5)),
        padding: "10px 30px", borderRadius: 40, background: "#FF2D55", color: "#fff", fontFamily: FONT, fontWeight: 900, fontSize: 34,
        letterSpacing: 2, boxShadow: `0 0 ${24 + 12 * Math.sin(f / 5)}px rgba(255,45,85,0.75)`, whiteSpace: "nowrap",
      }}>{alert}</div>}
    </>
  );
};

const IntroSting: React.FC = () => {
  const f = useCurrentFrame();
  if (f > INTRO + 2) return null;
  const pop = sp(f, 9);
  const move = interpolate(f, [12, INTRO], [0, 1], { ...clamp, easing: Easing.bezier(0.7, 0, 0.3, 1) });
  const bgOp = interpolate(f, [0, 10, 18], [1, 1, 0], clamp);
  const rays = interpolate(f, [0, 16], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 45%, ${C.purple}, ${C.ink} 70%)`, opacity: bgOp }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: (1 - rays) * bgOp }}>
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} style={{ position: "absolute", width: 14, height: 300 + rays * 900, background: i % 2 ? C.yellow : C.pink, rotate: `${i * 30}deg`, borderRadius: 7, opacity: 0.7 }} />
        ))}
      </AbsoluteFill>
      <div style={{
        position: "absolute", left: "50%", top: interpolate(move, [0, 1], [820, 128]), translate: "-50% -50%",
        scale: `${interpolate(move, [0, 1], [1.6 * pop, 0.0])}`, opacity: interpolate(move, [0.75, 1], [1, 0], clamp),
        display: "flex", flexDirection: "column", alignItems: "center", gap: 20,
      }}>
        <Bait size={220} mood="happy" /><Wordmark size={90} />
      </div>
    </AbsoluteFill>
  );
};

/* ---------- ведучий у кутку ---------- */
const CornerHost: React.FC<{ start: number; end: number; judgeFrom: number }> = ({ start, end, judgeFrom }) => {
  const f = useCurrentFrame(); const { mouth } = useEp();
  if (f < start || f > end) return null;
  const inS = start === 0 ? 1 : sp(f - start, 11); const out = interpolate(f, [end - 8, end], [1, 0], clamp);
  return (
    <div style={{ position: "absolute", right: 24, top: 975, opacity: out, translate: `${(1 - inS) * 300}px 0`, rotate: `${(1 - inS) * 20}deg`, filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.5))" }}>
      <Bait size={200} mouth={mouth[f] ?? 0} look={-6} mood={f >= judgeFrom ? "judge" : "talk"} />
    </div>
  );
};

/* ---------- гачок: великий заголовок з ПЕРШОГО кадру (28.10) ---------- */
const HookHeadline: React.FC<{ s: Scene }> = ({ s }) => {
  const f = useCurrentFrame();
  const text = s.hook ?? s.title;
  const parts = text.split(/(\*[^*]+\*)/g).filter(Boolean);
  const pulse = 1 + 0.025 * Math.sin(f / 6);
  return (
    <div style={{ position: "absolute", left: 50, right: 50, top: 210, display: "flex", justifyContent: "center", scale: `${pulse}` }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 108, lineHeight: 1.05, color: "white", textAlign: "center",
        textShadow: "0 8px 0 rgba(0,0,0,0.35), 0 0 40px rgba(124,92,255,0.6)", letterSpacing: -1 }}>
        {parts.map((p, i) => p.startsWith("*") ? <span key={i} style={{ color: C.yellow }}>{p.slice(1, -1)}</span> : <span key={i}>{p}</span>)}
      </div>
    </div>
  );
};

/* ---------- сцени ---------- */
const HookIcon: React.FC<{ s: Scene }> = ({ s }) => {
  const f = useCurrentFrame();
  const card = 0.9 + 0.1 * sp(f, 10); const badge = 0.85 + 0.15 * sp(f, 8); // з 28.10: видно з першого кадру (стрічка Shorts показує кадр 0)
  const ring = (d: number) => {
    const t = ((f + d) % 45) / 45;
    return <div style={{ position: "absolute", inset: -60 - t * 120, borderRadius: 140, border: `6px solid ${C.yellow}`, opacity: (1 - t) * 0.6 }} />;
  };
  return (
    <div style={{ position: "relative", scale: `${card}`, rotate: `${(1 - card) * -12}deg` }}>
      {ring(0)}{ring(22)}
      <div style={{
        width: 520, height: 520, borderRadius: 110, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`,
        display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 40px 90px rgba(124,92,255,0.6)",
        translate: `0 ${Math.sin(f / 10) * 10}px`,
      }}>
        <Icon name={s.icon ?? "bolt"} size={300} />
      </div>
      {s.badge ? <div style={{
        position: "absolute", right: -70, top: -40, scale: `${badge}`, rotate: `${12 + Math.sin(f / 8) * 4}deg`,
        background: s.badge ? "#FF2D55" : C.yellow, color: s.badge ? "#fff" : "#111", fontFamily: FONT, fontWeight: 900, fontSize: 60, padding: "16px 34px", borderRadius: 24, boxShadow: s.badge ? "0 0 40px rgba(255,45,85,0.8)" : "0 20px 40px rgba(0,0,0,0.4)",
      }}>{s.badge}</div> : null}
    </div>
  );
};

const List: React.FC<{ s: Scene; dur: number }> = ({ s, dur }) => {
  const f = useCurrentFrame();
  const items = (s.items ?? []) as [string, string][];
  const step = Math.max(14, Math.floor((dur - 30) / Math.max(1, items.length)));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 34, width: 860 }}>
      {items.map(([ic, tx], i) => {
        const a = 8 + i * step; const k = sp(f - a, 11);
        const active = f >= a && f < a + step + 6;
        return (
          <div key={i} style={{
            display: "flex", alignItems: "center", gap: 34, padding: "30px 40px", borderRadius: 36,
            background: active ? "rgba(255,214,10,0.16)" : "rgba(255,255,255,0.08)", border: `3px solid ${active ? C.yellow : "rgba(255,255,255,0.2)"}`,
            translate: `${(1 - k) * 400}px 0`, opacity: k, scale: active ? "1.04" : "1",
          }}>
            <div style={{ width: 120, height: 120, borderRadius: 30, background: `linear-gradient(135deg, ${C.purple}, ${C.pink})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Icon name={ic} size={76} />
            </div>
            <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 58, color: "white" }}>{tx}</div>
          </div>
        );
      })}
    </div>
  );
};

const BeforeAfter: React.FC<{ s: Scene }> = ({ s }) => {
  const f = useCurrentFrame();
  const l = sp(f - 4, 12); const r = sp(f - 30, 10);
  const strike = interpolate(f, [18, 30], [0, 1], clamp);
  const box = (title: string, text: string, good: boolean, k: number) => (
    <div style={{
      width: 420, height: 420, borderRadius: 50, padding: 36, display: "flex", flexDirection: "column", justifyContent: "space-between",
      background: good ? `linear-gradient(135deg, ${C.purple}, ${C.pink})` : "rgba(255,255,255,0.08)", border: good ? "none" : "3px solid rgba(255,255,255,0.2)",
      scale: `${k}`, opacity: k, boxShadow: good ? "0 30px 70px rgba(255,79,139,0.45)" : "none",
    }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 40, color: good ? C.yellow : "rgba(255,255,255,0.6)", letterSpacing: 2 }}>{title}</div>
      <div style={{ position: "relative", fontFamily: FONT, fontWeight: 900, fontSize: 60, color: good ? "white" : "rgba(255,255,255,0.75)", lineHeight: 1.1 }}>
        {text}
        {!good && <div style={{ position: "absolute", left: -10, right: -10, top: "50%", height: 10, borderRadius: 5, background: C.pink, transformOrigin: "left", scale: `${strike} 1` }} />}
      </div>
      <div style={{ alignSelf: "flex-end" }}><Icon name={good ? "check" : "text"} size={80} color={good ? "white" : "rgba(255,255,255,0.4)"} /></div>
    </div>
  );
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
      {box("БУЛО", s.before ?? "", false, l)}
      <svg width="80" height="80" viewBox="0 0 24 24" style={{ opacity: r }}><path d="M4 12h14M13 6l6 6-6 6" fill="none" stroke={C.yellow} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></svg>
      {box("СТАЛО", s.after ?? "", true, r)}
    </div>
  );
};

const MoneyList: React.FC<{ s: Scene; dur: number }> = ({ s, dur }) => {
  const f = useCurrentFrame();
  const coin = sp(f, 9);
  const items = (s.items ?? []) as string[];
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 40 }}>
      <div style={{ width: 300, height: 300, borderRadius: 150, background: `radial-gradient(circle at 35% 30%, #FFE76A, ${C.yellow} 55%, #C9A400)`,
        display: "flex", alignItems: "center", justifyContent: "center", scale: `${coin}`, rotate: `${Math.sin(f / 9) * 8}deg`, boxShadow: "0 0 80px rgba(255,214,10,0.55)" }}>
        <Icon name={s.icon ?? "money"} size={200} color="#5a4500" />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        {items.map((t, i) => {
          const k = sp(f - (dur * 0.35 + i * 14), 11);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 20, padding: "18px 34px", borderRadius: 26, background: "rgba(25,195,125,0.16)", border: `3px solid ${GREEN}`, scale: `${k}`, opacity: k }}>
              <Icon name="check" size={50} color={GREEN} />
              <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 46, color: "white" }}>{t}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const MoneyBig: React.FC<{ s: Scene; dur: number }> = ({ s, dur }) => {
  const f = useCurrentFrame();
  const k = sp(f - dur * 0.3, 8);
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}>
      <div style={{ scale: `${sp(f, 10)}` }}><Icon name="video" size={220} color={C.yellow} /></div>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 230, color: GREEN, scale: `${k}`, opacity: k, textShadow: "0 0 60px rgba(25,195,125,0.6)", lineHeight: 1 }}>{s.big}</div>
      <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 56, color: "white", opacity: k }}>{s.sub}</div>
      <div style={{ fontFamily: FONT, fontWeight: 600, fontSize: 30, color: "rgba(255,255,255,0.55)", opacity: k }}>{s.foot}</div>
    </div>
  );
};

const VerdictGeneric: React.FC<{ s: Scene }> = ({ s }) => {
  const f = useCurrentFrame();
  const sc = (s.score ?? 8) / 10;
  const p = interpolate(f, [8, 48], [0, sc], { ...clamp, easing: Easing.out(Easing.cubic) });
  const R = 200, Cc = 2 * Math.PI * R;
  const chip = (at: number, good: boolean, text?: string) => {
    const k = sp(f - at, 12);
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "16px 28px", borderRadius: 22, scale: `${k}`, opacity: k,
        background: good ? "rgba(25,195,125,0.18)" : "rgba(255,79,139,0.18)", border: `3px solid ${good ? GREEN : C.pink}`, fontFamily: FONT, fontWeight: 800, fontSize: 38, color: "white" }}>
        <span style={{ color: good ? GREEN : C.pink, fontSize: 48 }}>{good ? "+" : "−"}</span>{text}
      </div>
    );
  };
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 40 }}>
      <div style={{ position: "relative", width: 480, height: 480 }}>
        <svg width="480" height="480" viewBox="0 0 480 480" style={{ rotate: "-90deg" }}>
          <circle cx="240" cy="240" r={R} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="38" />
          <circle cx="240" cy="240" r={R} fill="none" stroke={C.yellow} strokeWidth="38" strokeLinecap="round" strokeDasharray={Cc} strokeDashoffset={Cc * (1 - p)} style={{ filter: `drop-shadow(0 0 18px ${C.yellow})` }} />
        </svg>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: FONT, color: "white" }}>
          <div style={{ fontWeight: 900, fontSize: 210, lineHeight: 1 }}>{Math.round(p * 10)}</div>
          <div style={{ fontWeight: 800, fontSize: 56, opacity: 0.7 }}>/ 10</div>
        </AbsoluteFill>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 18, alignItems: "center" }}>
        {chip(55, true, s.plus)}{chip(85, false, s.minus)}
      </div>
    </div>
  );
};

const Outro: React.FC<{ offset: number }> = ({ offset }) => {
  const f = useCurrentFrame(); const { mouth } = useEp();
  const host = sp(f, 10), wm = sp(f - 8, 11), tag = sp(f - 16, 12), btn = sp(f - 24, 10);
  const tap = 70, sub = f >= tap, pressed = f >= tap && f < tap + 5;
  const cx = interpolate(f, [40, 66], [900, 600], { ...clamp, easing: Easing.out(Easing.cubic) });
  const cy = interpolate(f, [40, 66], [1700, 1300], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 230 }}>
      <div style={{ scale: `${host}`, filter: "drop-shadow(0 30px 50px rgba(124,92,255,0.6))" }}>
        <Bait size={340} withBody mouth={mouth[f + offset] ?? 0} mood={f > tap + 10 ? "happy" : "talk"} />
      </div>
      <div style={{ marginTop: 30, marginBottom: 14, scale: `${wm}` }}><Wordmark size={120} /></div>
      <div style={{ marginTop: 26, opacity: tag, translate: `0 ${(1 - tag) * 30}px`, fontFamily: FONT, fontWeight: 800, fontSize: 50, color: "white" }}>
        <Highlight color="rgba(255,214,10,0.45)" progress={interpolate(f, [24, 44], [0, 1], clamp)}>ШІ без води.</Highlight> Щодня.
      </div>
      <div style={{ marginTop: 60, scale: `${btn * (pressed ? 0.92 : 1)}`, padding: "30px 64px", borderRadius: 60, background: sub ? "#3A3A4A" : "#FF2D2D",
        color: "white", fontFamily: FONT, fontWeight: 900, fontSize: 52, boxShadow: sub ? "none" : "0 0 50px rgba(255,45,45,0.6)" }}>{sub ? "Ви підписані ✓" : "ПІДПИСАТИСЬ"}</div>
      <div style={{ marginTop: 40, opacity: interpolate(f, [30, 42], [0, 1], clamp) }}><Socials scale={0.85} t={f - 30} /></div>
      <Cursor x={cx} y={cy} pressed={pressed} />
    </AbsoluteFill>
  );
};

const Card: React.FC<{ label: string; title: string }> = ({ label, title }) => {
  const f = useCurrentFrame();
  const l = sp(f - 4, 12), t = sp(f - 8, 11);
  return (
    <div style={{ position: "absolute", top: 1180, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
      <div style={{ background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 38, padding: "10px 26px", borderRadius: 14, letterSpacing: 2, scale: `${l}` }}>{label}</div>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: Math.min(64, Math.floor(980 / (title.length * 0.66))), color: "white", whiteSpace: "nowrap", translate: `0 ${(1 - t) * 40}px`, opacity: t, textShadow: "0 6px 20px rgba(0,0,0,0.6)" }}>{title}</div>
    </div>
  );
};

const Captions: React.FC = () => {
  const f = useCurrentFrame(); const { words: W, scenes } = useEp();
  const cur = W.find((w) => f >= w.s && f < w.e) ?? [...W].reverse().find((w) => f >= w.e && f < w.e + 8);
  if (!cur || cur.g.startsWith(`${scenes.length - 1}-`)) return null;
  const group = W.filter((w) => w.g === cur.g);
  const pop = sp(f - group[0].s, 10);
  return (
    <div style={{ position: "absolute", top: 1470, left: 50, right: 50, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 28px", scale: `${0.85 + 0.15 * pop}` }}>
      {group.map((w, i) => {
        const active = f >= w.s && f < w.e;
        return <span key={i} style={{ fontFamily: FONT, fontWeight: 900, fontSize: 74, color: active ? C.yellow : "white", WebkitTextStroke: "14px black", paintOrder: "stroke fill", lineHeight: 1.25, scale: active ? "1.08" : "1", display: "inline-block" }}>{w.w}</span>;
      })}
    </div>
  );
};

const Stage: React.FC<{ dur: number; children: React.ReactNode; first?: boolean }> = ({ dur, children, first }) => {
  const f = useCurrentFrame();
  const s = first ? 1 : sp(f, 14); const out = interpolate(f, [dur - 7, dur], [1, 0], clamp); // перша сцена — без появи: кадр 0 вже повний
  return (
    <AbsoluteFill style={{ top: first ? 470 : 210, height: 960, alignItems: "center", justifyContent: "center", opacity: Math.min(s * 1.4, 1) * out, translate: `0 ${(1 - s) * 80}px`, scale: `${0.9 + 0.1 * s}` }}>
      {children}
    </AbsoluteFill>
  );
};

export const GenericEpisode: React.FC<EpData> = (props) => {
  const sc = props.scenes;
  const vIdx = sc.findIndex((s) => s.kind.startsWith("verdict"));
  const oIdx = sc.findIndex((s) => s.kind === "outro");
  return (
    <Ctx.Provider value={props}>
      <AbsoluteFill style={{ fontFamily: FONT }}>
        <style>{fontCss}</style>
        <Background />
        {sc.map((s, i) => {
          const start = i === 0 ? 0 : s.from - 6;
          const end = i < sc.length - 1 ? sc[i + 1].from - 6 : props.total;
          const dur = end - start;
          if (s.kind === "outro") return <Sequence key={i} from={start} durationInFrames={dur}><Outro offset={start} /></Sequence>;
          const V = s.kind === "hookIcon" ? <HookIcon s={s} /> : s.kind === "list" ? <List s={s} dur={dur} /> : s.kind === "beforeAfter" ? <BeforeAfter s={s} />
            : s.kind === "moneyList" ? <MoneyList s={s} dur={dur} /> : s.kind === "moneyBig" ? <MoneyBig s={s} dur={dur} /> : <VerdictGeneric s={s} />;
          return (
            <Sequence key={i} from={start} durationInFrames={dur}>
              <Stage dur={dur} first={i === 0 && s.kind === "hookIcon"}>{V}</Stage>
              {i === 0 && s.kind === "hookIcon" ? <HookHeadline s={s} /> : <Card label={s.label} title={s.title} />}
            </Sequence>
          );
        })}
        {oIdx > 0 && <CornerHost start={0} end={sc[oIdx].from - 6} judgeFrom={vIdx >= 0 ? sc[vIdx].from - 6 : 99999} />}
        <Captions />
        <TopBrand />
        {/* IntroSting вимкнено 24.10: гачок з першого кадру */}
      </AbsoluteFill>
    </Ctx.Provider>
  );
};
