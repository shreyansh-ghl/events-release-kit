import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Grain } from "./components/Grain";
import { Subtitles } from "./components/Overlays";
import { loadFonts } from "./fonts";
import { Chapter } from "./scenes/Chapter";
import { ColdOpen, HANDOFF } from "./scenes/ColdOpen";
import { EndCard } from "./scenes/EndCard";
import { Interstitial } from "./scenes/Interstitial";
import { TitleCard } from "./scenes/TitleCard";
import { ReleaseProps, Scene } from "./types";

loadFonts();

const SceneView = ({ scene, prev, next, t }: { scene: Scene; prev?: Scene; next?: Scene; t: number }) => {
  switch (scene.kind) {
    case "cold_open":
      return <ColdOpen t={t} dur={scene.dur} beats={scene.beats.map((b) => ({ ...b, at: b.at - scene.from }))} payoff={{ ...scene.payoff, at: scene.payoff.at - scene.from }} prop={scene.prop} />;
    case "title":
      return <TitleCard t={t} dur={scene.dur} kicker={scene.kicker} headline={scene.headline} laptop={scene.laptop} handoff={next?.kind === "chapter"} early={prev?.kind === "cold_open" ? HANDOFF : 0} />;
    case "chapter":
      return <Chapter t={t} from={scene.from} dur={scene.dur} label={scene.label} color={scene.color} shots={scene.shots} />;
    case "interstitial":
      return <Interstitial t={t} dur={scene.dur} kicker={scene.kicker} word={scene.word} sub={scene.sub} />;
    case "end":
      return <EndCard t={t} tagline={scene.tagline} subline={scene.subline} available={scene.available} where={scene.where} product={scene.product} />;
  }
};

/** The whole release video: scenes back to back, VO clips, the ducked bed, subtitles and grain. */
export const Release = (props: ReleaseProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const f = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{ background: "#141310" }}>
      {props.scenes
        .map((s, i) => {
          const prev = props.scenes[i - 1];
          const early = s.kind === "title" && prev?.kind === "cold_open" ? HANDOFF : 0;
          return (
            <Sequence key={i} from={f(s.from - early)} durationInFrames={Math.max(1, f(s.from + s.dur) - f(s.from - early))} layout="none">
              <AbsoluteFill>
                <SceneView scene={s} prev={prev} next={props.scenes[i + 1]} t={t - s.from} />
              </AbsoluteFill>
            </Sequence>
          );
        })
        .reverse()}
      <Subtitles t={t} vo={props.vo} />
      <Grain frame={frame} />
      {props.vo.map((v) => (
        <Sequence key={v.id} from={f(v.at)} layout="none">
          <Audio src={staticFile(v.src)} />
        </Sequence>
      ))}
      {props.bed ? <Audio src={staticFile(props.bed)} /> : null}
    </AbsoluteFill>
  );
};

