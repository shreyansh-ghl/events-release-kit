import { AbsoluteFill } from "remotion";
import { ease, windowed } from "../anim";
import { Serif } from "../components/Serif";
import { LABEL, LOOK, PAPER_BG, SANS } from "../look";

/** A single serif word between sections ("Agenda", "LevelUp"), with an optional kicker and small line. */
export const Interstitial = ({ t, dur, kicker, word, sub }: { t: number; dur: number; kicker?: string; word: string; sub?: string }) => {
  const o = windowed(t, 0.1, dur, 0.5, 0.35);
  return (
    <AbsoluteFill style={{ background: PAPER_BG, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", opacity: o,
      filter: `blur(${(1 - ease(t, 0.1, 0.7)) * 10}px)` }}>
      {kicker ? <div style={{ fontFamily: LABEL, fontWeight: 500, fontSize: 15, letterSpacing: "0.3em", color: LOOK.muted, marginBottom: 22 }}>{kicker}</div> : null}
      <Serif text={word} style={{ fontSize: 120, color: LOOK.inkText }} />
      {sub ? <div style={{ fontFamily: SANS, fontSize: 20, color: LOOK.muted, marginTop: 18 }}>{sub}</div> : null}
    </AbsoluteFill>
  );
};
