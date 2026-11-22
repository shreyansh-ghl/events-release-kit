import { AbsoluteFill, Img as RImg, staticFile } from "remotion";
import { ease, windowed } from "../anim";
import { Serif } from "../components/Serif";
import { LABEL, LOOK, NIGHT_BG, SANS } from "../look";
import { Img } from "../types";

interface Props {
  t: number;
  dur: number;
  beats: { text: string; at: number }[];
  payoff: { text: string; at: number };
  prop?: { img: Img; width: number; pile?: { label: string; to: number; items: { from: string; subject: string }[]; hero: { from: string; subject: string } } };
}

/** The title fades in under the cold open's last HANDOFF seconds (film: paper + laptop appear behind "Not anymore."). */
export const HANDOFF = 1.2;

/** Deterministic pseudo-random in [0, 1). */
const rnd = (i: number) => {
  const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};

/**
 * The old pain on ink: one serif line per beat, an optional prop (e.g. the confirmation email) that piles up
 * into an endless grid with a running counter, then the turn ("Not anymore.").
 */
export const ColdOpen = ({ t, dur, beats, payoff, prop }: Props) => {
  const pileAt = beats.length > 1 ? beats[0].at + 0.75 : Infinity;
  const tiltAt = beats.length > 1 ? beats[1].at + 0.8 : Infinity;
  const clearAt = payoff.at - 0.55;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill style={{ background: NIGHT_BG, opacity: 1 - 0.6 * ease(t, dur - HANDOFF, dur - 0.3) - 0.4 * ease(t, dur - 0.3, dur) }} />
      {prop ? <Prop t={t} prop={prop} pileAt={pileAt} tiltAt={tiltAt} clearAt={clearAt} /> : null}
      {beats.map((b, i) => {
        const end = i + 1 < beats.length ? beats[i + 1].at - 0.05 : clearAt + 0.3;
        const o = windowed(t, b.at - 0.25, end, 0.45, 0.35);
        if (o <= 0.001) {
          return null;
        }
        return (
          <div key={i} style={{ position: "absolute", left: 0, right: 0, top: 70, textAlign: "center", opacity: o, filter: `blur(${(1 - o) * 10}px)` }}>
            <Serif text={b.text} style={{ fontSize: 96, lineHeight: "96px", color: LOOK.nightText }} />
          </div>
        );
      })}
      {(() => {
        const o = windowed(t, payoff.at - 0.15, dur, 0.5, 0.25);
        return o > 0.001 ? (
          <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", opacity: o, filter: `blur(${(1 - ease(t, payoff.at - 0.15, payoff.at + 0.5)) * 12}px)` }}>
            <Serif text={payoff.text} style={{ fontSize: 100, color: "#f6f2ea", textShadow: "0 2px 30px rgba(0,0,0,0.35)" }} />
          </AbsoluteFill>
        ) : null;
      })()}
    </AbsoluteFill>
  );
};

const COLS = 10;
const ROWS = 30;
const CW = 162; // inbox row size, measured from the film (1080p)
const CH = 30;
const GX = 7;
const GY = 6;
const AVATAR = ["#f59e0b", "#d946ef", "#3b82f6", "#10b981", "#ef4444", "#6366f1", "#14b8a6", "#f97316", "#64748b", "#22c55e"];

type Pile = { label: string; to: number; items: { from: string; subject: string }[]; hero: { from: string; subject: string } };

/** One inbox row (fictional sender + subject): the pile is drawn, not captured. */
const Row = ({ from, subject, color, hero = 0 }: { from: string; subject: string; color: string; hero?: number }) => (
  <div style={{ width: CW, height: CH, borderRadius: 5, background: "#f7f7f8", display: "flex", alignItems: "center", gap: 6, padding: "0 7px",
    boxShadow: `0 0 0 ${1.5 * hero}px #fa694c, 0 0 ${16 * hero}px rgba(250,105,76,${0.8 * hero})`, fontFamily: SANS, overflow: "hidden" }}>
    <div style={{ width: 15, height: 15, borderRadius: "50%", background: color, color: "#fff", fontSize: 8, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flex: "none" }}>
      {from[0]}
    </div>
    <div style={{ lineHeight: 1.05, minWidth: 0 }}>
      <div style={{ fontSize: 7.5, fontWeight: 700, color: "#101828", whiteSpace: "nowrap" }}>{from}</div>
      <div style={{ fontSize: 6.5, color: "#475467", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{subject}</div>
    </div>
  </div>
);

/** Cells ordered from the centre outward (slight jitter), so the inbox grows around the lost email. */
const ORDER = Array.from({ length: COLS * ROWS }, (_, i) => i)
  .map((i) => ({ i, d: Math.hypot((i % COLS) - (COLS - 1) / 2, (Math.floor(i / COLS) - 7) * 1.9) + rnd(i) * 1.4 }))
  .sort((a, b) => a.d - b.d)
  .map((c) => c.i);

const Prop = ({ t, prop, pileAt, tiltAt, clearAt }: { t: number; prop: NonNullable<Props["prop"]>; pileAt: number; tiltAt: number; clearAt: number }) => {
  const w = prop.width;
  const h = (prop.img.h / prop.img.w) * w;
  const pile = prop.pile as Pile | undefined;
  const enter = ease(t, 0.0, 0.7);
  const glow = windowed(t, pileAt - 0.25, pileAt + 1.4, 0.25, 0.4);
  const shrink = ease(t, pileAt + 0.2, pileAt + 0.95);
  const swap = ease(t, pileAt + 0.8, pileAt + 1.0);
  const fill = pile ? ease(t, pileAt + 0.6, tiltAt + 0.9, (x) => Math.pow(x, 1.25)) : 0;
  const tilt = ease(t, tiltAt, tiltAt + 1.5);
  const out = 1 - ease(t, clearAt - 0.1, clearAt + 0.45);
  const n = Math.round(COLS * ROWS * fill);
  const gridW = COLS * (CW + GX) - GX;
  const centre = ORDER[0];
  const cx = (centre % COLS) * (CW + GX);
  const cy = Math.floor(centre / COLS) * (CH + GY);
  const gridLeft = 960 - gridW / 2;
  const gridTop = 600 - CH / 2 - cy;
  // hero card flies from full size into the centre slot
  const tx = 960 + (gridLeft + cx + CW / 2 - 960) * shrink;
  const ty = 600 + (gridTop + cy + CH / 2 - 600) * shrink;
  const sw = w + (CW - w) * shrink;
  const sh = h + (CH - h) * shrink;
  const count = pile ? Math.round(Math.pow(fill, 1.1) * pile.to) : 0;
  return (
    <>
      <AbsoluteFill style={{ perspective: 1500, perspectiveOrigin: "50% 15%", opacity: out }}>
        <div style={{ position: "absolute", left: gridLeft, top: gridTop, width: gridW, transform: `translateY(${-tilt * 120}px) rotateX(${tilt * 50}deg) scale(${1 + tilt * 0.35})`,
          transformOrigin: `${cx + CW / 2}px ${cy}px` }}>
          {pile
            ? ORDER.slice(0, Math.max(n, swap > 0 ? 1 : 0)).map((cell, k) => {
                const isHero = cell === centre;
                const item = isHero ? pile.hero : pile.items[k % pile.items.length];
                const pop = isHero ? 1 : ease(fill * COLS * ROWS - k, 0, 5);
                return (
                  <div key={cell} style={{ position: "absolute", left: (cell % COLS) * (CW + GX), top: Math.floor(cell / COLS) * (CH + GY), opacity: (isHero ? swap : pop) * (isHero ? 1 : 0.9),
                    transform: `scale(${0.8 + 0.2 * pop})`, filter: isHero ? undefined : `brightness(${rnd(cell + 3) > 0.86 ? 0.62 : 0.94 + 0.06 * rnd(cell + 5)})` }}>
                    <Row from={item.from} subject={item.subject} color={AVATAR[(k * 7 + 3) % AVATAR.length]} hero={isHero ? glow : 0} />
                  </div>
                );
              })
            : null}
        </div>
      </AbsoluteFill>
      {swap < 1 ? (
        <div style={{ position: "absolute", left: tx - sw / 2, top: ty - sh / 2 + (1 - enter) * 40, width: sw, height: sh, opacity: enter * (1 - swap), borderRadius: 28 - 23 * shrink,
          overflow: "hidden", boxShadow: `0 40px 90px rgba(0,0,0,${0.55 * (1 - shrink)}), 0 0 0 ${4 * glow}px #fa694c, 0 0 ${60 * glow}px rgba(250,105,76,${0.7 * glow})` }}>
          <RImg src={staticFile(prop.img.src)} style={{ width: "100%", height: "100%", display: "block" }} />
        </div>
      ) : null}
      {pile && fill > 0 ? (
        <div style={{ position: "absolute", right: 72, top: 70, textAlign: "right", opacity: out * ease(fill, 0, 0.04), color: LOOK.nightText }}>
          <div style={{ fontFamily: LABEL, fontSize: 11, fontWeight: 600, letterSpacing: "0.22em", color: LOOK.nightMuted, marginBottom: 4 }}>INBOX</div>
          <span style={{ fontFamily: SANS, fontSize: 38, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{count.toLocaleString("en-US")}</span>
          <span style={{ fontFamily: SANS, fontSize: 15, fontWeight: 500, marginLeft: 8, color: LOOK.nightMuted }}>{pile.label}</span>
        </div>
      ) : null}
    </>
  );
};
