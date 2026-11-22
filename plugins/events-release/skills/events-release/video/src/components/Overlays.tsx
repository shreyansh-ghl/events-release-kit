import { LABEL, SANS } from "../look";
import { windowed } from "../anim";
import { VoCue } from "../types";

/** Every VO line as a dark pill, bottom centre (film: 1009–1051 px at 1080p). */
export const Subtitles = ({ t, vo }: { t: number; vo: VoCue[] }) => {
  const cue = vo.find((c) => c.sub && t >= c.at - 0.05 && t < c.at + c.dur + 0.3);
  if (!cue) {
    return null;
  }
  const o = windowed(t, cue.at - 0.05, cue.at + cue.dur + 0.3, 0.12, 0.15);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 29, display: "flex", justifyContent: "center", opacity: o }}>
      <div style={{ maxWidth: 1400, padding: "6px 15px 7px", borderRadius: 5, background: "rgba(34,32,29,0.86)", color: "#fff",
        fontFamily: SANS, fontSize: 24.5, fontWeight: 400, lineHeight: "29px", textAlign: "center" }}>
        {cue.text}
      </div>
    </div>
  );
};

/** Chapter label, top left: off-white pill, coloured bar, letter-spaced caps. */
export const ChapterLabel = ({ text, color, opacity }: { text: string; color: string; opacity: number }) => (
  <div style={{ position: "absolute", left: 56, top: 48, height: 43, display: "flex", alignItems: "center", gap: 13, padding: "0 20px 0 15px",
    borderRadius: 9, background: "rgba(249,248,245,0.96)", boxShadow: "0 8px 22px rgba(30,24,16,0.14), 0 1px 2px rgba(30,24,16,0.08)",
    opacity, transform: `translateY(${(1 - opacity) * -6}px)` }}>
    <div style={{ width: 3, height: 17, borderRadius: 2, background: color }} />
    <div style={{ fontFamily: LABEL, fontWeight: 600, fontSize: 19.5, letterSpacing: "0.26em", color: "#171512", textTransform: "uppercase", whiteSpace: "nowrap" }}>{text}</div>
  </div>
);
