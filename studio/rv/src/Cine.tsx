// Кінематографічний шаблон Shorts (28.10): камера, що не зупиняється, летить крізь неонові кільця-портали від сцени до сцени;
// жирна об'ємна типографіка (екструзія шарами в CSS 3D), скульптурні форми (кільця, сфери, куби). Ті самі props, що й Ep (prep_ep.py).
// Типи сцен: cineTitle {title, hook}, cinePrompt {text — промпт, що «друкується»}, cineReel {big, sub}, cineList {title, items[]}, cineVerdict {score, plus, minus, title}, outro.
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, Easing } from "remotion";
import { Bait, Wordmark, C, FONT, Socials } from "./brand";
import { fontCss } from "./parts";
import type { EpData, Scene } from "./Generic";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const DZ = 2600; // відстань між сценами в 3D
const NEON = C.yellow;

/* ---------- позиція камери: повільний дрейф у сцені + швидкий проліт крізь портал ---------- */
function camZ(f: number, sc: Scene[]) { return camState(f, sc).z; }
function camState(f: number, sc: Scene[]) {
  let z = 0, fly = 0;
  for (let i = 0; i < sc.length; i++) {
    const a = i === 0 ? 0 : sc[i].from, b = i + 1 < sc.length ? sc[i + 1].from : 1e9;
    if (f < a) break;
    const FL = 10; // кадрів на проліт (28.10: швидше, динамічніше)
    const hold = Math.max(1, b - a - FL);
    const t = f - a;
    if (t < hold) { z = i * DZ + interpolate(t, [0, hold], [0, 300], clamp); fly = 0; }
    else { const r = (t - hold) / FL; const k = interpolate(r, [0, 1], [0, 1], { ...clamp, easing: Easing.bezier(0.7, 0, 0.3, 1) }); z = i * DZ + 300 + k * (DZ - 300); fly = Math.sin(Math.PI * Math.min(1, r)); }
  }
  return { z, fly };
}

/* ---------- об'ємний текст: фронт + екструзія шарами ---------- */
const Extruded: React.FC<{ text: string; size: number; color?: string; depth?: number; accent?: boolean }> = ({ text, size, color = "white", depth = 16, accent }) => {
  const parts = text.split(/(\*[^*]+\*)/g).filter(Boolean);
  const render = (fill: (hl: boolean) => string, extra: React.CSSProperties = {}) => (
    <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 0.98, textAlign: "center", letterSpacing: -2, ...extra }}>
      {parts.map((p, i) => { const hl = p.startsWith("*"); return <span key={i} style={{ color: fill(hl) }}>{hl ? p.slice(1, -1) : p}</span>; })}
    </div>
  );
  return (
    <div style={{ position: "relative", transformStyle: "preserve-3d" }}>
      {Array.from({ length: depth }).map((_, k) => (
        <div key={k} style={{ position: k === 0 ? "relative" : "absolute", inset: 0, transform: `translateZ(${-(depth - k) * 4}px)`, visibility: k === 0 ? "hidden" : "visible" }}>
          {render((hl) => (hl || accent ? `rgb(${120 - k * 2},${70 + k * 3},${20})` : `rgb(${40 + k * 3},${20 + k * 2},${90 + k * 4})`))}
        </div>
      ))}
      <div style={{ position: "absolute", inset: 0, transform: "translateZ(0px)" }}>
        {render((hl) => (hl || accent ? NEON : color), { textShadow: `0 0 30px ${accent ? "rgba(255,214,10,0.55)" : "rgba(124,92,255,0.55)"}` })}
      </div>
    </div>
  );
};

/* ---------- скульптурні форми ---------- */
const Ring: React.FC<{ r: number; w?: number; color?: string; z?: number; tilt?: number; spin?: number }> = ({ r, w = 26, color = NEON, z = 0, tilt = 0, spin = 0 }) => (
  <div style={{ position: "absolute", left: "50%", top: "50%", width: r * 2, height: r * 2, marginLeft: -r, marginTop: -r, borderRadius: "50%",
    border: `${w}px solid ${color}`, boxShadow: `0 0 40px ${color}, inset 0 0 40px ${color}`, transform: `translateZ(${z}px) rotateX(${tilt}deg) rotateZ(${spin}deg)` }} />
);
const Sphere: React.FC<{ d: number; x: number; y: number; z: number; c1?: string; c2?: string }> = ({ d, x, y, z, c1 = C.purple, c2 = "#140c35" }) => (
  <div style={{ position: "absolute", left: "50%", top: "50%", width: d, height: d, marginLeft: -d / 2 + x, marginTop: -d / 2 + y, borderRadius: "50%",
    background: `radial-gradient(circle at 32% 30%, #fff 0%, ${c1} 22%, ${c2} 75%)`, transform: `translateZ(${z}px)`, boxShadow: `0 30px 80px rgba(0,0,0,0.5)` }} />
);
const Cube: React.FC<{ s: number; x: number; y: number; z: number; rot: number; color?: string }> = ({ s, x, y, z, rot, color = C.pink }) => {
  const face = (t: string, shade: number) => <div style={{ position: "absolute", width: s, height: s, transform: t, background: color, filter: `brightness(${shade})`, border: "2px solid rgba(255,255,255,0.25)" }} />;
  const h = s / 2;
  return (
    <div style={{ position: "absolute", left: "50%", top: "50%", width: s, height: s, marginLeft: -h + x, marginTop: -h + y, transformStyle: "preserve-3d", transform: `translateZ(${z}px) rotateX(${rot}deg) rotateY(${rot * 1.3}deg)` }}>
      {face(`translateZ(${h}px)`, 1)}{face(`rotateY(180deg) translateZ(${h}px)`, 0.5)}{face(`rotateY(90deg) translateZ(${h}px)`, 0.75)}
      {face(`rotateY(-90deg) translateZ(${h}px)`, 0.6)}{face(`rotateX(90deg) translateZ(${h}px)`, 1.15)}{face(`rotateX(-90deg) translateZ(${h}px)`, 0.4)}
    </div>
  );
};

/* ---------- сцени (локальний кадр t) ---------- */
const Typed: React.FC<{ text: string; t: number; dur: number; chips?: string[] }> = ({ text, t, dur, chips }) => {
  const n = Math.floor(interpolate(t, [6, Math.max(8, dur * 0.7)], [0, text.length], clamp));
  return (
    <div style={{ width: 720, padding: "40px 44px", borderRadius: 40, background: "rgba(18,12,40,0.88)", border: `3px solid ${NEON}`, boxShadow: `0 0 60px rgba(255,214,10,0.35)` }}>
      <div style={{ display: "flex", gap: 14, marginBottom: 26 }}>
        {(chips ?? ["ПРОМПТ", "ШІ", "МОУШН"]).map((x) => <span key={x} style={{ fontFamily: FONT, fontWeight: 900, fontSize: 26, color: "#111", background: NEON, borderRadius: 30, padding: "6px 18px" }}>{x}</span>)}
      </div>
      <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 44, lineHeight: 1.25, color: "white" }}>
        «{text.slice(0, n)}<span style={{ opacity: Math.floor(t / 8) % 2 ? 1 : 0, color: NEON }}>|</span>»
      </div>
    </div>
  );
};

const SceneBody: React.FC<{ s: Scene & any; t: number; dur: number; i: number }> = ({ s, t, dur, i }) => {
  const pop = spring({ frame: t, fps: 30, config: { damping: 13, mass: 0.7 } });
  const wob = Math.sin(t / 18) * 6;
  if (s.kind === "cineTitle") return (
    <div style={{ transformStyle: "preserve-3d", transform: `rotateY(${wob}deg) rotateX(${-wob / 2}deg)` }}>
      <Extruded text={s.hook ?? s.title} size={128} />
      <Ring r={430} w={22} z={-500} tilt={70} spin={t * 2} /><Sphere d={150} x={-380} y={-520} z={-300} /><Cube s={110} x={380} y={470} z={-200} rot={t * 2} />
    </div>
  );
  if (s.kind === "cinePrompt") return <div style={{ transform: `rotateY(${wob * 0.6}deg)`, scale: `${0.9 + 0.1 * pop}` }}><Typed text={s.text_prompt ?? s.title} t={t} dur={dur} chips={s.chips} /></div>;
  if (s.kind === "cineReel") return (
    <div style={{ transformStyle: "preserve-3d", transform: `rotateY(${Math.sin(t / 14) * 18}deg) rotateX(${Math.cos(t / 20) * 8}deg)` }}>
      {[0, 1, 2, 3, 4].map((k) => <Ring key={k} r={240 + k * 130} w={18} z={-k * 320} spin={t * (k % 2 ? -3 : 3)} color={k % 2 ? NEON : C.cyan} />)}
      <Extruded text={s.big} size={138} accent depth={22} />
      {s.sub && <div style={{ marginTop: 40, textAlign: "center" }}><Extruded text={s.sub} size={64} depth={8} /></div>}
      <Sphere d={120} x={-420} y={600} z={200} c1={C.pink} /><Cube s={90} x={420} y={-600} z={150} rot={t * 3} color={C.purple} />
    </div>
  );
  if (s.kind === "cineList") return (
    <div style={{ display: "flex", flexDirection: "column", gap: 36, alignItems: "center", transformStyle: "preserve-3d", transform: `rotateY(${wob}deg)` }}>
      <Extruded text={s.title} size={92} depth={10} accent />
      {(s.items ?? []).map((it: string, k: number) => {
        const a = spring({ frame: t - 10 - k * Math.max(12, (dur - 30) / Math.max(1, s.items.length)), fps: 30, config: { damping: 12 } });
        return <div key={k} style={{ width: 760, textAlign: "center", boxSizing: "border-box", transform: `translateZ(${(1 - a) * -900}px)`, opacity: a, fontFamily: FONT, fontWeight: 900, fontSize: 50, color: "white", background: "rgba(124,92,255,0.25)", border: `3px solid ${k % 2 ? C.cyan : NEON}`, borderRadius: 30, padding: "18px 36px" }}>{it}</div>;
      })}
    </div>
  );
  if (s.kind === "cineVerdict") return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 30, transformStyle: "preserve-3d", transform: `rotateY(${wob}deg)` }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 40, color: "#111", background: NEON, padding: "8px 26px", borderRadius: 30 }}>ВЕРДИКТ БАЙТА</div>
      <div style={{ transform: `scale(${0.6 + 0.4 * pop})`, transformStyle: "preserve-3d" }}><Extruded text={`*${s.score}*/10`} size={230} depth={24} /></div>
      <div style={{ width: 820, textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: 46, color: "#3DDC97" }}>+ {s.plus}</div>
      <div style={{ width: 820, textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: 46, color: "#FF5C7A" }}>− {s.minus}</div>
      <Ring r={360} w={16} z={-400} tilt={75} spin={t * 3} />
    </div>
  );
  return ( // outro: соцмережі
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 34, transform: `scale(${0.85 + 0.15 * pop})` }}>
      <Bait size={230} mood="happy" mouth={0} /><Wordmark size={96} />
      <Socials t={t - 6} />
    </div>
  );
};

/* ---------- субтитри ---------- */
const Captions: React.FC<{ d: EpData }> = ({ d }) => {
  const f = useCurrentFrame(); const W = d.words;
  const cur = W.find((w) => f >= w.s && f < w.e);
  if (!cur) return null;
  const group = W.filter((w) => w.g === cur.g);
  return (
    <div style={{ position: "absolute", top: 1380, left: 40, right: 40, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 26px" }}>
      {group.map((w, i) => {
        const a = f >= w.s && f < w.e; const k = spring({ frame: f - w.s, fps: 30, config: { damping: 9, mass: 0.5 } });
        const seen = f >= w.s;
        return <span key={i} style={{ display: "inline-block", fontFamily: FONT, fontWeight: 900, fontSize: 80, color: a ? NEON : "white", WebkitTextStroke: "13px black", paintOrder: "stroke fill",
          opacity: seen ? 1 : 0.25, transform: `scale(${seen ? 0.7 + 0.3 * k + (a ? 0.12 : 0) : 0.8}) rotate(${a ? (i % 2 ? 4 : -4) : 0}deg)` }}>{w.w}</span>;
      })}
    </div>
  );
};

export const Cine: React.FC<EpData> = (d) => {
  const f = useCurrentFrame(); const sc = d.scenes;
  const { z, fly } = camState(f, sc);
  const sway = Math.sin(f / 13) * 7, bob = Math.cos(f / 11) * 4;
  const roll = fly * 16 * (Math.floor(f / 60) % 2 ? 1 : -1);
  const punch = 1 + 0.035 * Math.max(0, Math.sin(f / 4.5)) ** 8; // ритмічні «удари» камери
  const idx = Math.max(0, sc.findIndex((s, i) => f >= (i === 0 ? 0 : s.from) && (i + 1 >= sc.length || f < sc[i + 1].from)));
  const last = sc.length - 1;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, #241656 0%, #0B0A1C 70%)`, overflow: "hidden" }}>
      <style>{fontCss}</style>
      {/* зоряний пил для відчуття швидкості */}
      <AbsoluteFill style={{ perspective: 900 }}>
        <div style={{ position: "absolute", inset: 0, transformStyle: "preserve-3d", transform: `translateZ(${z % 1200}px)` }}>
          {Array.from({ length: 60 }).map((_, k) => <div key={k} style={{ position: "absolute", left: `${(k * 37) % 100}%`, top: `${(k * 53) % 100}%`, width: 6, height: 6 + fly * 140, borderRadius: 3, background: k % 3 ? "#fff" : NEON, opacity: 0.5 + fly * 0.4, transform: `translateZ(${-((k * 97) % 1200)}px)` }} />)}
        </div>
      </AbsoluteFill>
      {/* світ сцен */}
      <AbsoluteFill style={{ perspective: 1100, perspectiveOrigin: "50% 45%", filter: `blur(${fly * 7}px)` }}>
        <div style={{ position: "absolute", left: "50%", top: "45%", transformStyle: "preserve-3d", transform: `scale(${punch}) rotateZ(${roll}deg) rotateY(${sway}deg) rotateX(${bob}deg) translateZ(${z}px)` }}>
          {sc.map((s, i) => {
            if (Math.abs(i - idx) > 1) return null;
            const a = i === 0 ? 0 : s.from; const b = i + 1 < sc.length ? sc[i + 1].from : d.total;
            const t = f - a;
            const dist = i * DZ - z; // >0 — сцена попереду камери
            const vis = interpolate(dist, [-700, -150, 0, DZ * 0.45, DZ * 0.75], [0, 1, 1, 1, 0], clamp); // наступна не просвічує, поки не підлетіли
            return (
              <React.Fragment key={i}>
                <div style={{ position: "absolute", transformStyle: "preserve-3d", opacity: vis, transform: `translate(-50%, -50%) translateZ(${-i * DZ}px)` }}>
                  <SceneBody s={s} t={Math.max(0, t)} dur={b - a} i={i} />
                </div>
                {i < last && <div style={{ position: "absolute", transformStyle: "preserve-3d", transform: `translateZ(${-i * DZ - DZ * 0.62}px)` }}><Ring r={760} w={34} spin={f * 1.5} /><Ring r={620} w={10} color={C.cyan} spin={-f * 2} /></div>}
              </React.Fragment>
            );
          })}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(255,255,255,0.9), rgba(255,214,10,0.5) 40%, transparent 75%)", opacity: fly ** 3 * 0.55, pointerEvents: "none" }} />
      {/* Байт і бренд поверх */}
      {idx < last && <div style={{ position: "absolute", right: 30, bottom: 520 }}><Bait size={190} mouth={d.mouth[f] ?? 0} mood={sc[idx]?.kind === "cineVerdict" ? "judge" : "talk"} /></div>}
      <div style={{ position: "absolute", top: 70, left: "50%", translate: "-50% 0", opacity: 0.9 }}><Wordmark size={46} /></div>
      {sc[idx]?.label && idx > 0 && <div style={{ position: "absolute", top: 170, left: "50%", translate: "-50% 0", fontFamily: FONT, fontWeight: 900, fontSize: 34, color: "#111", background: NEON, padding: "6px 22px", borderRadius: 26 }}>{sc[idx].label}</div>}
      <div style={{ position: "absolute", top: 0, left: 0, height: 10, width: `${(f / d.total) * 100}%`, background: NEON }} />
      <Captions d={d} />
    </AbsoluteFill>
  );
};
