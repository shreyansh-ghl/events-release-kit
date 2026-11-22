import { AbsoluteFill } from "remotion";

const NOISE = `url("data:image/svg+xml;utf8,${encodeURIComponent(
  "<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.1 0 0 0 0 0.09 0 0 0 0 0.08 0 0 0 0.9 0'/></filter><rect width='100%' height='100%' filter='url(#n)'/></svg>",
)}")`;

/** Fine film grain over every frame; the offset moves each frame so it reads as grain, not a texture. */
export const Grain = ({ frame, opacity = 0.05 }: { frame: number; opacity?: number }) => (
  <AbsoluteFill style={{ backgroundImage: NOISE, backgroundPosition: `${(frame * 37) % 220}px ${(frame * 53) % 220}px`, opacity, pointerEvents: "none" }} />
);
