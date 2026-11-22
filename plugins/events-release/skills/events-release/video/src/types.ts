/**
 * Resolved release props. scripts/release_video.py turns a release spec into this shape:
 * every time is absolute seconds from the start of the video, every image carries its pixel size.
 */
export interface Img {
  src: string; // path inside the render's public dir
  w: number;
  h: number;
}

export interface VoCue {
  id: string;
  src: string;
  text: string;
  at: number;
  dur: number;
  sub: boolean; // false: the line is already on screen (cold open), no subtitle pill
}

export interface Cam {
  t: number; // seconds from shot start
  x: number; // world point at the frame centre (world = 1920x1080 title layout)
  y: number;
  zoom: number;
}

export interface Shot {
  from: number;
  dur: number;
  laptop?: { img: Img; url: string; scroll?: [number, number][]; swaps?: { t: number; img: Img }[] };
  phone?: { img: Img; enter?: number; swaps?: { t: number; img: Img }[] };
  focus?: [number, "laptop" | "phone"][];
  camera: Cam[];
  cursor?: [number, number, number, ("click" | null)?][]; // [t, x, y, click] in laptop screenshot px
  tap?: [number, number, number][]; // [t, x, y] in phone screenshot px
}

export type Scene =
  | { kind: "cold_open"; from: number; dur: number; beats: { text: string; at: number }[]; payoff: { text: string; at: number };
      prop?: { img: Img; width: number; pile?: { label: string; to: number; items: { from: string; subject: string }[]; hero: { from: string; subject: string } } } }
  | { kind: "title"; from: number; dur: number; kicker: string; headline: string; laptop: { img: Img; url: string } }
  | { kind: "chapter"; from: number; dur: number; label: string; color: string; shots: Shot[] }
  | { kind: "interstitial"; from: number; dur: number; kicker?: string; word: string; sub?: string }
  | { kind: "end"; from: number; dur: number; tagline: string; subline: string; available: string; where: string; product: string };

export interface ReleaseProps {
  fps: number;
  width: number;
  height: number;
  total: number; // seconds
  scenes: Scene[];
  vo: VoCue[];
  bed: string | null; // music + effects, already ducked under the VO
  [key: string]: unknown;
}
