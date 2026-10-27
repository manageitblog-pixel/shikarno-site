import React from "react";
import {
  AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile, Easing,
} from "remotion";
import data from "./data.json";

const ACC = "#FFD60A";
const PURPLE = "#7C5CFF";
const PINK = "#FF4F8B";
const TEAL = "#00C8AA";
const BLUE = "#3C8CFF";
const ORANGE = "#FFA028";
const FONT = "Mont";

const fontCss = `@font-face{font-family:'${FONT}';src:url('${staticFile("Montserrat.ttf")}') format('truetype');font-weight:100 900;}`;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const useSpring = (delay = 0, damping = 12) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - delay, fps, config: { damping, mass: 0.8 } });
};

/* ---------------- фон ---------------- */
const Background: React.FC = () => {
  const f = useCurrentFrame();
  const a = f / 30;
  const blob = (x: number, y: number, size: number, color: string) => (
    <div style={{
      position: "absolute", left: x - size / 2, top: y - size / 2, width: size, height: size,
      borderRadius: "50%", background: color, filter: "blur(120px)", opacity: 0.55,
    }} />
  );
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#0B0A1C 0%,#140F33 55%,#1A1240 100%)" }}>
      {blob(540 + Math.cos(a * 0.5) * 320, 520 + Math.sin(a * 0.7) * 200, 700, PURPLE)}
      {blob(540 + Math.sin(a * 0.4) * 360, 1350 + Math.cos(a * 0.6) * 220, 600, PINK)}
      {blob(540 + Math.cos(a * 0.3 + 2) * 300, 950 + Math.sin(a * 0.5) * 250, 500, "#00A3FF")}
      <AbsoluteFill style={{
        backgroundImage: "linear-gradient(rgba(255,255,255,0.045) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.045) 2px, transparent 2px)",
        backgroundSize: "90px 90px", backgroundPosition: `0 ${(f * 1.2) % 90}px`,
        maskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)",
      }} />
    </AbsoluteFill>
  );
};

/* ---------------- верхня плашка ---------------- */
const TopBar: React.FC = () => {
  const f = useCurrentFrame();
  const p = f / data.total;
  return (
    <>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 12, background: "rgba(255,255,255,0.12)" }}>
        <div style={{ width: `${p * 100}%`, height: "100%", background: ACC }} />
      </div>
      <div style={{
        position: "absolute", top: 100, left: "50%", transform: "translateX(-50%)",
        display: "flex", alignItems: "center", gap: 16, padding: "16px 34px", borderRadius: 50,
        background: "rgba(255,255,255,0.10)", border: "2px solid rgba(255,255,255,0.25)",
        fontFamily: FONT, fontWeight: 800, fontSize: 38, color: "white", letterSpacing: 1,
        backdropFilter: "blur(10px)",
      }}>
        <div style={{ width: 18, height: 18, borderRadius: 9, background: "#FF3B5C", opacity: Math.floor(f / 15) % 2 ? 0.35 : 1, boxShadow: "0 0 16px #FF3B5C" }} />
        AI ЗА 40 СЕКУНД
      </div>
    </>
  );
};

/* ---------------- примітиви ---------------- */
const Shirt: React.FC<{ color: string; w?: number }> = ({ color, w = 300 }) => (
  <svg width={w} height={w * 0.9} viewBox="0 0 200 180">
    <path d="M60 10 L140 10 L195 45 L170 90 L150 78 L150 175 L50 175 L50 78 L30 90 L5 45 Z" fill={color} />
    <path d="M78 10 Q100 38 122 10" fill="#E8B49A" />
  </svg>
);

const Jacket: React.FC<{ w?: number }> = ({ w = 220 }) => (
  <svg width={w} height={w} viewBox="0 0 200 200">
    <path d="M65 15 L135 15 L180 45 L195 185 L160 185 L150 80 L150 190 L50 190 L50 80 L40 185 L5 185 L20 45 Z" fill={ORANGE} />
    <path d="M65 15 L100 60 L135 15" fill="none" stroke="#B9650F" strokeWidth="8" />
    <line x1="100" y1="60" x2="100" y2="190" stroke="#B9650F" strokeWidth="6" />
    <rect x="62" y="120" width="26" height="8" rx="4" fill="#B9650F" />
    <rect x="112" y="120" width="26" height="8" rx="4" fill="#B9650F" />
  </svg>
);

const Person: React.FC<{ shirt: React.ReactNode }> = ({ shirt }) => (
  <div style={{ position: "relative", width: 340, height: 520, display: "flex", flexDirection: "column", alignItems: "center" }}>
    <div style={{ width: 150, height: 150, borderRadius: "50%", background: "#E8B49A", marginTop: 40 }} />
    <div style={{ width: 54, height: 34, background: "#DCA488", marginTop: -8 }} />
    <div style={{ marginTop: -14 }}>{shirt}</div>
  </div>
);

/* Футболка, що змінює колір «скан-лінією» */
const TryOnShirt: React.FC<{ from: string; to: string; start: number; dur?: number; w?: number }> = ({ from, to, start, dur = 24, w = 300 }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [start, start + dur], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const h = w * 0.9;
  return (
    <div style={{ position: "relative", width: w, height: h }}>
      <div style={{ position: "absolute", inset: 0 }}><Shirt color={from} w={w} /></div>
      <div style={{ position: "absolute", inset: 0, clipPath: `inset(0 0 ${(1 - p) * 100}% 0)` }}><Shirt color={to} w={w} /></div>
      {p > 0 && p < 1 && (
        <div style={{ position: "absolute", left: -30, right: -30, top: p * h - 4, height: 8, background: ACC, borderRadius: 4, boxShadow: `0 0 30px 10px ${ACC}88` }} />
      )}
    </div>
  );
};

const Phone: React.FC<{ children: React.ReactNode; scale?: number }> = ({ children, scale = 1 }) => (
  <div style={{
    width: 500 * scale, height: 860 * scale, borderRadius: 80 * scale, background: "#16161F",
    border: `${6 * scale}px solid #4A4A66`, padding: 22 * scale, boxShadow: "0 40px 80px rgba(0,0,0,0.55)",
  }}>
    <div style={{
      position: "relative", width: "100%", height: "100%", borderRadius: 58 * scale, overflow: "hidden",
      background: "linear-gradient(180deg,#F4F3FF,#E4E1FA)", display: "flex", flexDirection: "column", alignItems: "center",
    }}>
      <div style={{ width: 130 * scale, height: 36 * scale, borderRadius: 18 * scale, background: "#16161F", marginTop: 16 * scale }} />
      {children}
    </div>
  </div>
);

const Cursor: React.FC<{ x: number; y: number; pressed?: boolean }> = ({ x, y, pressed }) => (
  <svg style={{ position: "absolute", left: x, top: y, transform: `scale(${pressed ? 0.85 : 1})`, filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.5))" }} width="90" height="110" viewBox="0 0 24 30">
    <path d="M2 1 L2 23 L8 17.5 L12 27 L16 25.3 L12 16 L20 16 Z" fill="white" stroke="#111" strokeWidth="1.6" strokeLinejoin="round" />
  </svg>
);

const Stage: React.FC<{ children: React.ReactNode; dur: number }> = ({ children, dur }) => {
  const f = useCurrentFrame();
  const s = useSpring(0, 14);
  const out = interpolate(f, [dur - 7, dur], [1, 0], clamp);
  return (
    <AbsoluteFill style={{
      top: 210, height: 960, alignItems: "center", justifyContent: "center",
      opacity: Math.min(s * 1.4, 1) * out, transform: `translateY(${(1 - s) * 80}px) scale(${0.9 + 0.1 * s})`,
    }}>
      {children}
    </AbsoluteFill>
  );
};

/* ---------------- сцени ---------------- */
const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const badge = useSpring(10, 8);
  const float = Math.sin(f / 12) * 10;
  return (
    <div style={{ position: "relative", transform: `translateY(${float}px)` }}>
      <Phone scale={0.95}>
        <div style={{ marginTop: 30 }}>
          <Person shirt={<TryOnShirt from={PURPLE} to={PINK} start={20} />} />
        </div>
      </Phone>
      <div style={{
        position: "absolute", right: -120, top: 60, transform: `scale(${badge}) rotate(${12 + Math.sin(f / 8) * 4}deg)`,
        background: ACC, color: "#111", fontFamily: FONT, fontWeight: 900, fontSize: 56, padding: "18px 34px", borderRadius: 24,
        boxShadow: "0 20px 40px rgba(0,0,0,0.4)",
      }}>НОВЕ!</div>
    </div>
  );
};

const Selfie: React.FC = () => {
  const f = useCurrentFrame();
  const flash = interpolate(f, [18, 22, 34], [0, 1, 0], clamp);
  const corner = (r: number) => (
    <div style={{
      position: "absolute", width: 70, height: 70, border: `8px solid ${ACC}`, transform: `rotate(${r}deg)`,
      borderRight: "none", borderBottom: "none", borderRadius: "14px 0 0 0",
      ...(r === 0 ? { left: 40, top: 110 } : r === 90 ? { right: 40, top: 110 } : r === 180 ? { right: 40, bottom: 140 } : { left: 40, bottom: 140 }),
    }} />
  );
  return (
    <Phone>
      <div style={{ marginTop: 40 }}>
        <Person shirt={<TryOnShirt from={PINK} to={TEAL} start={45} dur={30} />} />
      </div>
      {[0, 90, 180, 270].map((r) => <React.Fragment key={r}>{corner(r)}</React.Fragment>)}
      <div style={{ position: "absolute", bottom: 40, width: 110, height: 110, borderRadius: 55, border: "8px solid #16161F", background: "white" }} />
      <AbsoluteFill style={{ background: "white", opacity: flash }} />
    </Phone>
  );
};

const Screenshot: React.FC = () => {
  const f = useCurrentFrame();
  const card = useSpring(0, 12);
  const phone = useSpring(22, 12);
  const arrowP = interpolate(f, [16, 40], [0, 1], clamp);
  const fly = interpolate(f, [40, 62], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  return (
    <div style={{ position: "relative", width: 1000, height: 900 }}>
      {/* вікно браузера */}
      <div style={{
        position: "absolute", left: 20, top: 40, width: 420, height: 520, borderRadius: 30, background: "white",
        transform: `rotate(-6deg) scale(${card})`, boxShadow: "0 30px 60px rgba(0,0,0,0.5)", overflow: "hidden",
      }}>
        <div style={{ height: 60, background: "#E9E9F2", display: "flex", alignItems: "center", gap: 12, paddingLeft: 24 }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <div key={c} style={{ width: 20, height: 20, borderRadius: 10, background: c }} />)}
          <div style={{ marginLeft: 14, width: 220, height: 28, borderRadius: 14, background: "white" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginTop: 40, opacity: 1 - fly * 0.6 }}><Jacket w={240} /></div>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 52, color: "#111", textAlign: "center", marginTop: 26 }}>2 499 ₴</div>
        {/* «спалах» скріншота */}
        <AbsoluteFill style={{ border: `10px solid ${ACC}`, borderRadius: 30, opacity: interpolate(f, [10, 14, 26], [0, 1, 0], clamp) }} />
      </div>
      {/* стрілка */}
      <svg style={{ position: "absolute", left: 360, top: 250 }} width="260" height="160" viewBox="0 0 260 160">
        <path d="M10 130 Q130 -10 240 80" fill="none" stroke={ACC} strokeWidth="10" strokeLinecap="round"
          strokeDasharray="320" strokeDashoffset={320 * (1 - arrowP)} />
        {arrowP > 0.95 && <path d="M215 50 L245 85 L205 95" fill="none" stroke={ACC} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
      {/* телефон */}
      <div style={{ position: "absolute", right: 0, top: 120, transform: `scale(${phone})` }}>
        <Phone scale={0.82}>
          <div style={{ position: "relative", marginTop: 30 }}>
            <Person shirt={<Shirt color={TEAL} />} />
            <div style={{ position: "absolute", left: 20, top: 175, opacity: fly, transform: `scale(${0.6 + 0.6 * fly})`, transformOrigin: "top center" }}>
              <Jacket w={300} />
            </div>
          </div>
        </Phone>
      </div>
    </div>
  );
};

const Star: React.FC = () => {
  const f = useCurrentFrame();
  const star = useSpring(0, 9);
  const items: [string, string][] = [["Куртка", "1 899 ₴"], ["Джинси", "1 299 ₴"], ["Кросівки", "2 750 ₴"]];
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 50 }}>
      <div style={{
        width: 300, height: 300, borderRadius: 40, background: `linear-gradient(135deg, ${PURPLE}, ${PINK})`,
        display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${star}) rotate(${(1 - star) * -30}deg)`,
        boxShadow: "0 30px 70px rgba(124,92,255,0.6)",
      }}>
        <svg width="190" height="190" viewBox="0 0 24 24" style={{ transform: `rotate(${f * 0.8}deg)` }}>
          <path d="M12 1.8l3.1 6.4 7 1-5.1 4.9 1.2 7-6.2-3.3-6.2 3.3 1.2-7L1.9 9.2l7-1z" fill={ACC} />
        </svg>
      </div>
      <div style={{ display: "flex", gap: 30 }}>
        {items.map(([n, p], i) => {
          const s = spring({ frame: f - 25 - i * 9, fps: 30, config: { damping: 11 } });
          return (
            <div key={n} style={{
              width: 280, padding: "34px 0", borderRadius: 30, background: "white", textAlign: "center",
              transform: `translateY(${(1 - s) * 200}px) scale(${s})`, opacity: s, boxShadow: "0 20px 40px rgba(0,0,0,0.4)",
            }}>
              <div style={{ width: 70, height: 70, borderRadius: 35, background: TEAL, margin: "0 auto 18px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="44" height="44" viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="white" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </div>
              <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 40, color: "#111" }}>{n}</div>
              <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 34, color: "#666", marginTop: 8 }}>{p}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const TryOnButton: React.FC = () => {
  const f = useCurrentFrame();
  const tap = 52;
  const cx = interpolate(f, [8, 46], [700, 300], { ...clamp, easing: Easing.out(Easing.cubic) });
  const cy = interpolate(f, [8, 46], [1000, 690], { ...clamp, easing: Easing.out(Easing.cubic) });
  const pressed = f >= tap && f < tap + 6;
  const ripple = interpolate(f, [tap, tap + 20], [0, 1], clamp);
  return (
    <div style={{ position: "relative" }}>
      <Phone>
        <div style={{ marginTop: 20 }}>
          <Person shirt={<TryOnShirt from={TEAL} to={BLUE} start={tap + 4} />} />
        </div>
        <div style={{
          position: "absolute", bottom: 70, width: 340, height: 100, borderRadius: 50, background: "#111",
          display: "flex", alignItems: "center", justifyContent: "center", gap: 16, transform: `scale(${pressed ? 0.92 : 1 + Math.sin(f / 5) * 0.03})`,
          fontFamily: FONT, fontWeight: 800, fontSize: 46, color: "white", boxShadow: `0 0 ${40 * (1 - ripple)}px ${ACC}`,
        }}>
          <svg width="44" height="44" viewBox="0 0 24 24"><path d="M9 3h6l5 3-2 5-2-1v10H8V10l-2 1-2-5z" fill={ACC} /></svg>
          Try On
        </div>
        {ripple > 0 && ripple < 1 && (
          <div style={{
            position: "absolute", bottom: 120 - 250 * ripple, left: "50%", width: 500 * ripple, height: 500 * ripple,
            marginLeft: -250 * ripple, borderRadius: "50%", border: `8px solid ${ACC}`, opacity: 1 - ripple,
          }} />
        )}
      </Phone>
      <Cursor x={cx} y={cy} pressed={pressed} />
    </div>
  );
};

const Rating: React.FC = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, [5, 45], [0, 0.8], { ...clamp, easing: Easing.out(Easing.cubic) });
  const R = 260, C = 2 * Math.PI * R;
  const done = useSpring(46, 8);
  return (
    <div style={{ position: "relative", width: 640, height: 640 }}>
      <svg width="640" height="640" viewBox="0 0 640 640" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="320" cy="320" r={R} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="44" />
        <circle cx="320" cy="320" r={R} fill="none" stroke={ACC} strokeWidth="44" strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={C * (1 - p)} style={{ filter: `drop-shadow(0 0 20px ${ACC})` }} />
      </svg>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: FONT, color: "white" }}>
        <div style={{ fontWeight: 900, fontSize: 280, lineHeight: 1, transform: `scale(${1 + done * 0.08})` }}>{Math.round(p * 10)}</div>
        <div style={{ fontWeight: 800, fontSize: 70, opacity: 0.7 }}>/ 10</div>
      </AbsoluteFill>
    </div>
  );
};

const Subscribe: React.FC = () => {
  const f = useCurrentFrame();
  const tap = 30;
  const cx = interpolate(f, [4, 26], [820, 640], { ...clamp, easing: Easing.out(Easing.cubic) });
  const cy = interpolate(f, [4, 26], [760, 520], { ...clamp, easing: Easing.out(Easing.cubic) });
  const sub = f >= tap;
  const bell = sub ? Math.sin((f - tap) * 1.2) * 22 * Math.exp(-(f - tap) / 14) : 0;
  const pressed = f >= tap && f < tap + 5;
  return (
    <div style={{ position: "relative", width: 900, height: 700, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 50 }}>
      <div style={{
        width: 220, height: 220, borderRadius: 110, background: `linear-gradient(135deg, ${PURPLE}, ${PINK})`,
        display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT, fontWeight: 900, fontSize: 90, color: "white",
        boxShadow: "0 20px 60px rgba(124,92,255,0.6)",
      }}>AI</div>
      <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
        <div style={{
          padding: "34px 60px", borderRadius: 60, background: sub ? "#3A3A4A" : "#FF2D2D", color: "white",
          fontFamily: FONT, fontWeight: 800, fontSize: 52, transform: `scale(${pressed ? 0.92 : 1})`,
          boxShadow: sub ? "none" : "0 0 40px rgba(255,45,45,0.6)",
        }}>{sub ? "Ви підписані" : "ПІДПИСАТИСЬ"}</div>
        <svg width="100" height="100" viewBox="0 0 24 24" style={{ transform: `rotate(${bell}deg)`, transformOrigin: "50% 10%" }}>
          <path d="M12 2a6 6 0 0 0-6 6v4l-2 4h16l-2-4V8a6 6 0 0 0-6-6zm-2.5 16a2.5 2.5 0 0 0 5 0z" fill={sub ? ACC : "white"} />
        </svg>
      </div>
      <Cursor x={cx} y={cy} pressed={pressed} />
    </div>
  );
};

const VISUALS = [Hook, Selfie, Screenshot, Star, TryOnButton, Rating, Subscribe];

/* ---------------- картка сцени ---------------- */
const Card: React.FC<{ label: string; title: string }> = ({ label, title }) => {
  const l = useSpring(2, 12);
  const t = useSpring(6, 10);
  return (
    <div style={{ position: "absolute", top: 1170, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 22 }}>
      <div style={{
        background: ACC, color: "#111", fontFamily: FONT, fontWeight: 900, fontSize: 40, padding: "10px 26px",
        borderRadius: 14, letterSpacing: 2, transform: `scale(${l})`,
      }}>{label}</div>
      <div style={{
        fontFamily: FONT, fontWeight: 900, fontSize: 70, color: "white", textAlign: "center", padding: "0 40px", whiteSpace: "nowrap",
        transform: `translateY(${(1 - t) * 40}px)`, opacity: t, textShadow: "0 6px 20px rgba(0,0,0,0.6)",
      }}>{title}</div>
    </div>
  );
};

/* ---------------- субтитри ---------------- */
const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const words = data.words;
  const cur = words.find((w) => f >= w.s && f < w.e) ?? [...words].reverse().find((w) => f >= w.e && f < w.e + 8);
  if (!cur) return null;
  const group = words.filter((w) => w.g === cur.g);
  const gs = group[0].s;
  const pop = spring({ frame: f - gs, fps: 30, config: { damping: 10, mass: 0.6 } });
  return (
    <div style={{
      position: "absolute", top: 1470, left: 50, right: 50, display: "flex", flexWrap: "wrap", justifyContent: "center",
      gap: "0 30px", transform: `scale(${0.85 + 0.15 * pop})`,
    }}>
      {group.map((w, i) => {
        const active = f >= w.s && f < w.e;
        return (
          <span key={i} style={{
            fontFamily: FONT, fontWeight: 900, fontSize: 74, color: active ? ACC : "white",
            WebkitTextStroke: "14px black", paintOrder: "stroke fill", lineHeight: 1.25,
            transform: `scale(${active ? 1.08 : 1})`, display: "inline-block",
          }}>{w.w}</span>
        );
      })}
    </div>
  );
};

export const Short: React.FC = () => {
  const sc = data.scenes;
  return (
    <AbsoluteFill style={{ fontFamily: FONT }}>
      <style>{fontCss}</style>
      <Background />
      {sc.map((s, i) => {
        const start = i === 0 ? 0 : s.from - 6;
        const end = i < sc.length - 1 ? sc[i + 1].from - 6 : data.total;
        const V = VISUALS[i];
        return (
          <Sequence key={i} from={start} durationInFrames={end - start}>
            <Stage dur={end - start}><V /></Stage>
            <Card label={s.label} title={s.title} />
          </Sequence>
        );
      })}
      <Captions />
      <TopBar />
    </AbsoluteFill>
  );
};
