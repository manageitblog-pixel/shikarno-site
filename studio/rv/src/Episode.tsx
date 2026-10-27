import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, Easing, staticFile } from "remotion";
import { Highlight, Circle as RCircle } from "@remotion/rough-notation";
import ep from "./ep.json";
import { Bait, Wordmark, Avatar, C, FONT } from "./brand";
import { Background, Phone, Person, Shirt, Jacket, TryOnShirt, Cursor, Hook, Selfie, Screenshot, fontCss, TEAL, BLUE } from "./parts";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const sp = (f: number, damping = 12) => spring({ frame: f, fps: 30, config: { damping, mass: 0.8 } });
const mouthAt = (f: number) => ep.mouth[Math.max(0, Math.min(ep.mouth.length - 1, f))] ?? 0;
const INTRO = 26;

/* ---------- верхня плашка з брендом ---------- */
const TopBrand: React.FC = () => {
  const f = useCurrentFrame();
  const show = sp(f - INTRO + 4, 14);
  return (
    <>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 12, background: "rgba(255,255,255,0.12)" }}>
        <div style={{ width: `${(f / ep.total) * 100}%`, height: "100%", background: C.yellow }} />
      </div>
      <div style={{
        position: "absolute", top: 92, left: "50%", translate: "-50% 0", scale: `${show}`, opacity: show,
        display: "flex", alignItems: "center", gap: 18, padding: "10px 30px 10px 12px", borderRadius: 60,
        background: "rgba(14,11,36,0.55)", border: "2px solid rgba(255,255,255,0.22)", backdropFilter: "blur(12px)",
      }}>
        <Avatar size={72} />
        <Wordmark size={46} />
      </div>
    </>
  );
};

/* ---------- заставка: логотип «влітає» і стає плашкою ---------- */
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
      {/* промені */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: (1 - rays) * bgOp }}>
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} style={{
            position: "absolute", width: 14, height: 300 + rays * 900, background: i % 2 ? C.yellow : C.pink,
            rotate: `${i * 30}deg`, borderRadius: 7, opacity: 0.7,
          }} />
        ))}
      </AbsoluteFill>
      <div style={{
        position: "absolute", left: "50%", top: interpolate(move, [0, 1], [820, 128]),
        translate: "-50% -50%", scale: `${interpolate(move, [0, 1], [1.6 * pop, 0.0])}`,
        opacity: interpolate(move, [0.75, 1], [1, 0], clamp), display: "flex", flexDirection: "column", alignItems: "center", gap: 20,
      }}>
        <Bait size={220} mood="happy" />
        <Wordmark size={90} />
      </div>
    </AbsoluteFill>
  );
};

/* ---------- ведучий у кутку ---------- */
const CornerHost: React.FC<{ start: number; end: number; judgeFrom: number }> = ({ start, end, judgeFrom }) => {
  const f = useCurrentFrame();
  const inS = sp(f - start, 11);
  const out = interpolate(f, [end - 8, end], [1, 0], clamp);
  if (f < start || f > end) return null;
  return (
    <div style={{
      position: "absolute", right: 34, top: 900, opacity: out, translate: `${(1 - inS) * 300}px 0`, rotate: `${(1 - inS) * 20}deg`,
      filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.5))",
    }}>
      <Bait size={230} mouth={mouthAt(f)} look={-6} mood={f >= judgeFrom ? "judge" : "talk"} />
    </div>
  );
};

/* ---------- сцена «як заробити» ---------- */
const Bubble: React.FC<{ me?: boolean; at: number; children: React.ReactNode }> = ({ me, at, children }) => {
  const f = useCurrentFrame();
  const s = sp(f - at, 12);
  return (
    <div style={{
      alignSelf: me ? "flex-end" : "flex-start", maxWidth: 330, padding: "18px 24px", borderRadius: 30,
      borderBottomRightRadius: me ? 8 : 30, borderBottomLeftRadius: me ? 30 : 8,
      background: me ? `linear-gradient(135deg, ${C.purple}, ${C.pink})` : "white", color: me ? "white" : "#111",
      fontFamily: FONT, fontWeight: 700, fontSize: 30, scale: `${s}`, opacity: s, transformOrigin: me ? "right bottom" : "left bottom",
      boxShadow: "0 8px 20px rgba(0,0,0,0.15)",
    }}>{children}</div>
  );
};

const Money: React.FC = () => {
  const f = useCurrentFrame();
  const sale = sp(f - 120, 10);
  const sum = Math.round(interpolate(f, [120, 170], [0, 2499], clamp));
  return (
    <div style={{ position: "relative" }}>
      <Phone>
        <div style={{ width: "100%", padding: "20px 26px", display: "flex", alignItems: "center", gap: 16, borderBottom: "2px solid #DDD" }}>
          <div style={{ width: 64, height: 64, borderRadius: 32, background: `linear-gradient(135deg, ${C.yellow}, ${C.pink})` }} />
          <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 30, color: "#111" }}>твій_магазин</div>
        </div>
        <div style={{ width: "100%", padding: "26px 24px", display: "flex", flexDirection: "column", gap: 20 }}>
          <Bubble at={10}>А як ця куртка буде на мені?</Bubble>
          <Bubble me at={45}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{ width: 120, height: 150, borderRadius: 18, background: "#EEE", display: "flex", alignItems: "flex-end", justifyContent: "center", overflow: "hidden" }}>
                <div style={{ scale: "0.36", transformOrigin: "bottom center", marginBottom: -40 }}><Person shirt={<Jacket w={300} />} /></div>
              </div>
              Ось твоя примірка
            </div>
          </Bubble>
          <Bubble at={95}>Ого! Беру!</Bubble>
        </div>
      </Phone>
      <div style={{
        position: "absolute", left: -150, top: 600, scale: `${sale}`, rotate: "-8deg",
        background: "#19C37D", color: "white", fontFamily: FONT, fontWeight: 900, fontSize: 58, padding: "18px 34px", borderRadius: 26,
        boxShadow: "0 20px 50px rgba(25,195,125,0.55)",
      }}>+{sum.toLocaleString("uk-UA")} ₴</div>
    </div>
  );
};

/* ---------- вердикт ---------- */
const Verdict: React.FC = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, [8, 48], [0, 0.8], { ...clamp, easing: Easing.out(Easing.cubic) });
  const R = 200, Cc = 2 * Math.PI * R;
  const chip = (at: number, good: boolean, text: string) => {
    const s = sp(f - at, 12);
    return (
      <div style={{
        display: "flex", alignItems: "center", gap: 14, padding: "16px 28px", borderRadius: 22, scale: `${s}`, opacity: s,
        background: good ? "rgba(25,195,125,0.18)" : "rgba(255,79,139,0.18)", border: `3px solid ${good ? "#19C37D" : C.pink}`,
        fontFamily: FONT, fontWeight: 800, fontSize: 38, color: "white",
      }}>
        <span style={{ color: good ? "#19C37D" : C.pink, fontSize: 48 }}>{good ? "+" : "−"}</span>{text}
      </div>
    );
  };
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 40 }}>
      <div style={{ position: "relative", width: 480, height: 480 }}>
        <svg width="480" height="480" viewBox="0 0 480 480" style={{ rotate: "-90deg" }}>
          <circle cx="240" cy="240" r={R} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="38" />
          <circle cx="240" cy="240" r={R} fill="none" stroke={C.yellow} strokeWidth="38" strokeLinecap="round"
            strokeDasharray={Cc} strokeDashoffset={Cc * (1 - p)} style={{ filter: `drop-shadow(0 0 18px ${C.yellow})` }} />
        </svg>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: FONT, color: "white" }}>
          <div style={{ fontWeight: 900, fontSize: 210, lineHeight: 1 }}>{Math.round(p * 10)}</div>
          <div style={{ fontWeight: 800, fontSize: 56, opacity: 0.7 }}>/ 10</div>
        </AbsoluteFill>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 18, alignItems: "center" }}>
        {chip(60, true, "Менше покупок наосліп")}
        {chip(100, false, "Поки лише картинка")}
      </div>
    </div>
  );
};

/* ---------- кінцева картка ---------- */
const Outro: React.FC = () => {
  const f = useCurrentFrame();
  const host = sp(f, 10);
  const wm = sp(f - 8, 11);
  const tag = sp(f - 16, 12);
  const btn = sp(f - 24, 10);
  const tap = 70;
  const sub = f >= tap;
  const pressed = f >= tap && f < tap + 5;
  const cx = interpolate(f, [40, 66], [900, 600], { ...clamp, easing: Easing.out(Easing.cubic) });
  const cy = interpolate(f, [40, 66], [1700, 1300], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 330 }}>
      <div style={{ scale: `${host}`, filter: "drop-shadow(0 30px 50px rgba(124,92,255,0.6))" }}>
        <Bait size={430} withBody mouth={mouthAt(f + ep.scenes[5].from - 6)} mood={f > tap + 10 ? "happy" : "talk"} />
      </div>
      <div style={{ marginTop: 30, marginBottom: 14, scale: `${wm}` }}><Wordmark size={120} /></div>
      <div style={{ marginTop: 26, opacity: tag, translate: `0 ${(1 - tag) * 30}px`, fontFamily: FONT, fontWeight: 800, fontSize: 50, color: "white" }}>
        <Highlight color="rgba(255,214,10,0.45)" progress={interpolate(f, [24, 44], [0, 1], clamp)}>ШІ без води.</Highlight> Щодня.
      </div>
      <div style={{
        marginTop: 60, scale: `${btn * (pressed ? 0.92 : 1)}`, padding: "30px 64px", borderRadius: 60,
        background: sub ? "#3A3A4A" : "#FF2D2D", color: "white", fontFamily: FONT, fontWeight: 900, fontSize: 52,
        boxShadow: sub ? "none" : "0 0 50px rgba(255,45,45,0.6)",
      }}>{sub ? "Ви підписані ✓" : "ПІДПИСАТИСЬ"}</div>
      <Cursor x={cx} y={cy} pressed={pressed} />
    </AbsoluteFill>
  );
};

/* ---------- картка сцени ---------- */
const Card: React.FC<{ label: string; title: string }> = ({ label, title }) => {
  const f = useCurrentFrame();
  const l = sp(f - 4, 12), t = sp(f - 8, 11);
  return (
    <div style={{ position: "absolute", top: 1180, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
      <div style={{ background: C.yellow, color: C.ink, fontFamily: FONT, fontWeight: 900, fontSize: 38, padding: "10px 26px", borderRadius: 14, letterSpacing: 2, scale: `${l}` }}>{label}</div>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 66, color: "white", whiteSpace: "nowrap", translate: `0 ${(1 - t) * 40}px`, opacity: t, textShadow: "0 6px 20px rgba(0,0,0,0.6)" }}>{title}</div>
    </div>
  );
};

/* ---------- субтитри ---------- */
const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const W = ep.words;
  const cur = W.find((w) => f >= w.s && f < w.e) ?? [...W].reverse().find((w) => f >= w.e && f < w.e + 8);
  if (!cur || cur.g.startsWith("5-")) return null;
  const group = W.filter((w) => w.g === cur.g);
  const pop = sp(f - group[0].s, 10);
  return (
    <div style={{ position: "absolute", top: 1470, left: 50, right: 50, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 28px", scale: `${0.85 + 0.15 * pop}` }}>
      {group.map((w, i) => {
        const active = f >= w.s && f < w.e;
        return (
          <span key={i} style={{
            fontFamily: FONT, fontWeight: 900, fontSize: 74, color: active ? C.yellow : "white",
            WebkitTextStroke: "14px black", paintOrder: "stroke fill", lineHeight: 1.25, scale: active ? "1.08" : "1", display: "inline-block",
          }}>{w.w}</span>
        );
      })}
    </div>
  );
};

const Stage: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const f = useCurrentFrame();
  const s = sp(f, 14);
  const out = interpolate(f, [dur - 7, dur], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ top: 210, height: 960, alignItems: "center", justifyContent: "center", opacity: Math.min(s * 1.4, 1) * out, translate: `0 ${(1 - s) * 80}px`, scale: `${0.9 + 0.1 * s}` }}>
      {children}
    </AbsoluteFill>
  );
};

const VIS: Record<string, React.FC> = { hook: Hook, selfie: Selfie, screenshot: Screenshot, money: Money, verdict: Verdict };

export const Episode: React.FC = () => {
  const sc = ep.scenes;
  return (
    <AbsoluteFill style={{ fontFamily: FONT }}>
      <style>{fontCss}</style>
      <Background />
      {sc.map((s, i) => {
        const start = i === 0 ? 0 : s.from - 6;
        const end = i < sc.length - 1 ? sc[i + 1].from - 6 : ep.total;
        if (s.kind === "outro") return <Sequence key={i} from={start} durationInFrames={end - start}><Outro /></Sequence>;
        const V = VIS[s.kind];
        return (
          <Sequence key={i} from={start} durationInFrames={end - start}>
            <Stage dur={end - start}><V /></Stage>
            <Card label={s.label} title={s.title} />
          </Sequence>
        );
      })}
      <CornerHost start={30} end={sc[5].from - 6} judgeFrom={sc[4].from - 6} />
      <Captions />
      <TopBrand />
      <IntroSting />
    </AbsoluteFill>
  );
};

/* ---------- стоп-кадри для оформлення каналу ---------- */
export const AvatarStill: React.FC = () => (
  <AbsoluteFill style={{ background: C.ink, alignItems: "center", justifyContent: "center" }}>
    <style>{fontCss}</style>
    <Avatar size={800} />
  </AbsoluteFill>
);

export const WatermarkStill: React.FC = () => (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
    <style>{fontCss}</style>
    <Avatar size={150} />
  </AbsoluteFill>
);

export const BannerStill: React.FC = () => {
  const chips = ["ChatGPT", "Gemini", "Claude", "Midjourney", "Sora", "AI-гроші", "Лайфхаки", "Вердикт 8/10"];
  const pos = [[180, 260], [2080, 230], [300, 1120], [2150, 1080], [230, 690], [2130, 690], [700, 1260], [1700, 1290]];
  return (
    <AbsoluteFill style={{ fontFamily: FONT }}>
      <style>{fontCss}</style>
      <Background />
      {chips.map((c, i) => (
        <div key={c} style={{
          position: "absolute", left: pos[i][0], top: pos[i][1], rotate: `${(i % 2 ? 1 : -1) * (4 + i)}deg`,
          padding: "14px 30px", borderRadius: 40, border: "3px solid rgba(255,255,255,0.25)", background: "rgba(255,255,255,0.07)",
          color: "rgba(255,255,255,0.75)", fontWeight: 800, fontSize: 44,
        }}>{c}</div>
      ))}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 46 }}>
        <Bait size={250} mood="happy" />
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Wordmark size={128} />
          <div style={{ fontWeight: 800, fontSize: 46, color: "white" }}>ШІ без води. <span style={{ color: C.yellow }}>Щодня.</span></div>
          <div style={{ fontWeight: 700, fontSize: 34, color: "rgba(255,255,255,0.7)" }}>Новини штучного інтелекту за 40 секунд</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
