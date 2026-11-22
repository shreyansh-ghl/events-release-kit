/**
 * World layout, measured from the film's title frame (1920x1080). The camera moves over this world;
 * at zoom 1 centred on (960, 540) the world is exactly the title card.
 */
export const W = 1920;
export const H = 1080;

/** Laptop screen rectangle (inside the bezel) and its browser bar. */
export const LAPTOP = { x: 385, y: 254, w: 1151, h: 718, bar: 28, bezel: 14 };
/** Visible page area under the browser bar. */
export const VIEWPORT = { x: LAPTOP.x, y: LAPTOP.y + LAPTOP.bar, w: LAPTOP.w, h: LAPTOP.h - LAPTOP.bar };

/** Phone placement when it joins the laptop (right side, overlapping the laptop's edge). */
export const PHONE = { x: 1365, y: 150, w: 390 };
export const PHONE_RATIO = 2.073; // outer height / width (house phone frame)
export const PHONE_BEZEL = 0.038;
export const PHONE_RADIUS = 0.163;

/** Default camera: the title framing. */
export const HOME = { x: W / 2, y: H / 2, zoom: 1 };
