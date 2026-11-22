import { Img as RImg, staticFile } from "remotion";
import { PHONE, PHONE_BEZEL, PHONE_RADIUS, PHONE_RATIO } from "../geometry";
import { Img } from "../types";

/** House phone frame in world space (same proportions as the screenshot cards). */
export const Phone = ({ img, next, mix = 0, dx = 0 }: { img: Img; next?: Img; mix?: number; dx?: number }) => {
  const w = PHONE.w;
  const h = w * PHONE_RATIO;
  const bz = w * PHONE_BEZEL;
  const r = w * PHONE_RADIUS;
  const screen = (im: Img, opacity: number) => (
    <RImg src={staticFile(im.src)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", objectPosition: "top center", opacity }} />
  );
  return (
    <div style={{ position: "absolute", left: PHONE.x + dx, top: PHONE.y, width: w, height: h, borderRadius: r, background: "#11100f",
      boxShadow: "0 40px 80px rgba(30,24,16,0.28), 0 10px 24px rgba(30,24,16,0.18)" }}>
      <div style={{ position: "absolute", left: bz, top: bz, right: bz, bottom: bz, borderRadius: r - bz, overflow: "hidden", background: "#fafafa" }}>
        {screen(img, 1)}
        {next && mix > 0 ? screen(next, mix) : null}
      </div>
      <div style={{ position: "absolute", left: "50%", top: bz + w * 0.021, width: w * 0.294, height: w * 0.1, marginLeft: -w * 0.147, borderRadius: w * 0.05, background: "#0b0a0a" }} />
    </div>
  );
};

/** Phone screenshot px → world px. */
export const phoneToWorld = (img: Img, x: number, y: number, dx = 0): [number, number] => {
  const w = PHONE.w;
  const bz = w * PHONE_BEZEL;
  const sw = w - 2 * bz;
  const sh = w * PHONE_RATIO - 2 * bz;
  const k = Math.max(sw / img.w, sh / img.h); // object-fit: cover, top aligned
  return [PHONE.x + dx + bz + (sw - img.w * k) / 2 + x * k, PHONE.y + bz + y * k];
};
