import { Composition } from "remotion";
import { Release } from "./Release";
import { ReleaseProps } from "./types";

const EMPTY: ReleaseProps = { fps: 60, width: 1920, height: 1080, total: 1, scenes: [], vo: [], bed: null };

export const RemotionRoot = () => (
  <>
    <Composition
      id="Release"
      component={Release}
      defaultProps={EMPTY}
      fps={60}
      width={1920}
      height={1080}
      durationInFrames={60}
      calculateMetadata={({ props }) => ({
        fps: props.fps,
        width: props.width,
        height: props.height,
        durationInFrames: Math.max(1, Math.ceil(props.total * props.fps)),
      })}
    />
  </>
);
