import { AbsoluteFill } from "remotion";
import { ease } from "../anim";
import { HighLevelMark } from "../components/HighLevelMark";
import { Serif } from "../components/Serif";
import { LOOK, NIGHT_BG, SANS, SERIF } from "../look";

const rise = (t: number, at: number) => {
  const o = ease(t, at, at + 0.7);
  return { opacity: o, transform: `translateY(${(1 - o) * 14}px)`, filter: `blur(${(1 - o) * 8}px)` };
};

/** Ink end card: mark, tagline, one grey line, "Available now" + where to find it, product wordmark. */
export const EndCard = ({ t, tagline, subline, available, where, product }: { t: number; tagline: string; subline: string; available: string; where: string; product: string }) => (
  <AbsoluteFill style={{ background: NIGHT_BG, opacity: ease(t, 0, 0.5) }}>
    <div style={{ position: "absolute", left: 0, right: 0, top: 225, display: "flex", justifyContent: "center", ...rise(t, 0.3) }}>
      <HighLevelMark height={116} />
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, top: 389, textAlign: "center", ...rise(t, 0.7) }}>
      <Serif text={tagline} style={{ fontSize: 109, lineHeight: "110px", color: LOOK.nightText }} />
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, top: 640, textAlign: "center", fontFamily: SANS, fontSize: 26, color: "rgba(243,239,231,0.66)", ...rise(t, 1.4) }}>{subline}</div>
    <div style={{ position: "absolute", left: 0, right: 0, top: 712, display: "flex", justifyContent: "center", alignItems: "center", gap: 18, fontFamily: SANS, fontSize: 22.5, ...rise(t, 1.9) }}>
      <div style={{ height: 45, display: "flex", alignItems: "center", gap: 10, padding: "0 19px 0 18px", borderRadius: 23, border: "1.5px solid rgba(243,239,231,0.32)", color: "#fff", fontWeight: 600 }}>
        <span style={{ width: 8, height: 8, borderRadius: "50%", background: LOOK.green }} />
        {available}
      </div>
      <div style={{ color: "rgba(243,239,231,0.62)" }}>{where}</div>
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, top: 808, display: "flex", justifyContent: "center", alignItems: "center", gap: 12, fontFamily: SERIF, fontSize: 39, color: LOOK.nightText, ...rise(t, 2.4) }}>
      <span>HighLevel</span>
      <span style={{ width: 1.5, height: 36, background: "rgba(243,239,231,0.45)" }} />
      <em style={{ fontStyle: "italic" }}>{product}</em>
    </div>
  </AbsoluteFill>
);
