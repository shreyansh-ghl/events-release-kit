import { Easing, interpolate } from "remotion";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0→1 over [a, b] seconds with the house ease (gentle in, soft out). */
export const ease = (t: number, a: number, b: number, fn = Easing.bezier(0.33, 0, 0.15, 1)): number =>
  b <= a ? (t >= b ? 1 : 0) : interpolate(t, [a, b], [0, 1], { ...clamp, easing: fn });

/** Fade in over [a, a+i], hold, fade out over [b-o, b]. */
export const windowed = (t: number, a: number, b: number, i = 0.35, o = 0.35): number =>
  Math.min(ease(t, a, a + i), 1 - ease(t, b - o, b));

/** Piecewise interpolation over keyframes [[t, v], ...] with the house ease between keys. */
export const keyed = (t: number, keys: [number, number][]): number => {
  if (!keys.length) {
    return 0;
  }
  if (t <= keys[0][0]) {
    return keys[0][1];
  }
  for (let i = 1; i < keys.length; i++) {
    const [t0, v0] = keys[i - 1];
    const [t1, v1] = keys[i];
    if (t <= t1) {
      return v0 + (v1 - v0) * ease(t, t0, t1);
    }
  }
  return keys[keys.length - 1][1];
};
