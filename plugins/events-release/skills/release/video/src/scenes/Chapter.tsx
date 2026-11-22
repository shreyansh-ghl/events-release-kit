import { AbsoluteFill } from "remotion";
import { ease, keyed, windowed } from "../anim";
import { Finger, Pointer } from "../components/Hand";
import { Laptop, laptopToWorld } from "../components/Laptop";
import { ChapterLabel } from "../components/Overlays";
import { Phone, phoneToWorld } from "../components/Phone";
import { H, HOME, W } from "../geometry";
import { PAPER_BG } from "../look";
import { Img, Shot } from "../types";

/** Image showing at shot time t: the base image or the latest swap; `mix` cross-fades over 0.25 s. */
const swapState = (base: Img, swaps: { t: number; img: Img }[] | undefined, t: number): { img: Img; next?: Img; mix: number } => {
  let img = base;
  for (const s of swaps ?? []) {
    if (t >= s.t + 0.25) {
      img = s.img;
    } else if (t >= s.t) {
      return { img, next: s.img, mix: ease(t, s.t, s.t + 0.25) };
    }
  }
  return { img, mix: 0 };
};

const camAt = (shot: Shot, t: number) => {
  const keys = shot.camera.length ? shot.camera : [{ t: 0, ...HOME }];
  return {
    x: keyed(t, keys.map((k) => [k.t, k.x])),
    y: keyed(t, keys.map((k) => [k.t, k.y])),
    zoom: keyed(t, keys.map((k) => [k.t, k.zoom])),
  };
};

/** Pointer position and press at time t from [t, x, y, click] keys (laptop screenshot px). */
const cursorAt = (keys: NonNullable<Shot["cursor"]>, t: number) => {
  const x = keyed(t, keys.map((k) => [k[0], k[1]]));
  const y = keyed(t, keys.map((k) => [k[0], k[2]]));
  const press = Math.max(0, ...keys.filter((k) => k[3] === "click").map((k) => windowed(t, k[0] - 0.02, k[0] + 0.22, 0.06, 0.16)));
  return { x, y, press, show: windowed(t, keys[0][0] - 0.3, keys[keys.length - 1][0] + 0.8, 0.3, 0.4) };
};

const ShotView = ({ shot, t }: { shot: Shot; t: number }) => {
  const cam = camAt(shot, t);
  const focusPhone = keyed(t, (shot.focus ?? [[0, "laptop"]]).map(([ft, f]) => [ft, f === "phone" ? 1 : 0]));
  const lap = shot.laptop ? swapState(shot.laptop.img, shot.laptop.swaps, t) : null;
  const scroll = shot.laptop?.scroll ? keyed(t, shot.laptop.scroll) : 0;
  const ph = shot.phone ? swapState(shot.phone.img, shot.phone.swaps, t) : null;
  const phoneIn = shot.phone ? ease(t, shot.phone.enter ?? 0, (shot.phone.enter ?? 0) + 0.9) : 0;
  const dx = (1 - phoneIn) * 900;
  const world = `translate(${W / 2}px, ${H / 2}px) scale(${cam.zoom}) translate(${-cam.x}px, ${-cam.y}px)`;
  const toFrame = ([wx, wy]: [number, number]): [number, number] => [W / 2 + (wx - cam.x) * cam.zoom, H / 2 + (wy - cam.y) * cam.zoom];

  let pointer = null;
  if (shot.cursor && shot.laptop && lap) {
    const c = cursorAt(shot.cursor, t);
    const [fx, fy] = toFrame(laptopToWorld(lap.img, scroll, c.x, c.y));
    pointer = <Pointer x={fx} y={fy} press={c.press} show={c.show} />;
  }
  let finger = null;
  if (shot.tap && shot.phone && ph) {
    const keys = shot.tap;
    const x = keyed(t, keys.map((k) => [k[0], k[1]]));
    const y = keyed(t, keys.map((k) => [k[0], k[2]]));
    const press = Math.max(0, ...keys.map((k) => windowed(t, k[0] - 0.05, k[0] + 0.3, 0.12, 0.2)));
    const show = windowed(t, keys[0][0] - 0.5, keys[keys.length - 1][0] + 0.9, 0.4, 0.45);
    const [wx, wy] = phoneToWorld(ph.img, x, y, dx);
    finger = <Finger x={wx} y={wy} press={press} show={show} scale={0.62} />;
  }
  return (
    <AbsoluteFill style={{ background: PAPER_BG, overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: world, transformOrigin: "0 0" }}>
        {shot.laptop && lap ? (
          <AbsoluteFill style={{ filter: shot.phone ? `blur(${focusPhone * 9}px)` : undefined }}>
            <Laptop img={lap.img} url={shot.laptop.url} scroll={scroll} next={lap.next} mix={lap.mix} />
          </AbsoluteFill>
        ) : null}
        {shot.phone && ph && phoneIn > 0 ? (
          <AbsoluteFill style={{ filter: shot.laptop ? `blur(${(1 - focusPhone) * 9}px)` : undefined }}>
            <Phone img={ph.img} next={ph.next} mix={ph.mix} dx={dx} />
            {finger}
          </AbsoluteFill>
        ) : null}
      </AbsoluteFill>
      {pointer}
    </AbsoluteFill>
  );
};

/** One chapter: label top left for its whole length, shots played back to back. */
export const Chapter = ({ t, from, dur, label, color, shots }: { t: number; from: number; dur: number; label: string; color: string; shots: Shot[] }) => {
  const abs = from + t;
  const shot = [...shots].reverse().find((s) => abs >= s.from) ?? shots[0];
  return (
    <AbsoluteFill>
      <ShotView shot={shot} t={abs - shot.from} />
      <ChapterLabel text={label} color={color} opacity={windowed(t, 0.35, dur, 0.4, 0.3)} />
    </AbsoluteFill>
  );
};
