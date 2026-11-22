import { AbsoluteFill } from "remotion";
import { ease, windowed } from "../anim";
import { Laptop } from "../components/Laptop";
import { Serif } from "../components/Serif";
import { LABEL, LOOK, PAPER_BG } from "../look";
import { Img } from "../types";

/**
 * "HIGHLEVEL" kicker + "Introducing the <feature>." over the laptop. The laptop sits exactly where a chapter's
 * camera starts (HOME), so title → first chapter is one continuous push-in. `handoff` fades the text out at the end.
 */
export const TitleCard = ({ t, dur, kicker, headline, laptop, handoff, early = 0 }: { t: number; dur: number; kicker: string; headline: string; laptop: { img: Img; url: string }; handoff: boolean; early?: number }) => {
  const rise = ease(t, -early, -early + 0.9);
  const text = windowed(t, 0.45, handoff ? dur : dur + 1, 0.6, 0.45);
  return (
    <AbsoluteFill style={{ background: PAPER_BG }}>
      <AbsoluteFill style={{ opacity: rise, transform: `translateY(${(1 - rise) * 70}px)` }}>
        <Laptop img={laptop.img} url={laptop.url} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 0, right: 0, top: 69, textAlign: "center", opacity: text, filter: `blur(${(1 - ease(t, 0.45, 1.05)) * 10}px)` }}>
        <div style={{ fontFamily: LABEL, fontWeight: 500, fontSize: 21, letterSpacing: "0.3em", color: "#4d4943", marginLeft: "0.3em" }}>{kicker}</div>
        <Serif text={headline} style={{ fontSize: 102, marginTop: 24, color: LOOK.inkText, whiteSpace: "nowrap" }} />
      </div>
    </AbsoluteFill>
  );
};
