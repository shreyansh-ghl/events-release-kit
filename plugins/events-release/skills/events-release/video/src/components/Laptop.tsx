import { Img as RImg, staticFile } from "remotion";
import { LAPTOP, VIEWPORT } from "../geometry";
import { Img } from "../types";
import { LOOK, SANS } from "../look";

const LIGHTS = ["#ff5f57", "#febc2e", "#28c840"];

/**
 * MacBook-style laptop in world space with a browser bar and a captured page.
 * `scroll` is in screenshot px; `next` cross-fades in (e.g. a toggle switching on) with `mix` 0→1.
 */
export const Laptop = ({ img, url, scroll = 0, next, mix = 0 }: { img: Img; url: string; scroll?: number; next?: Img; mix?: number }) => {
  const page = (im: Img, opacity: number) => {
    const k = VIEWPORT.w / im.w;
    return <RImg src={staticFile(im.src)} style={{ position: "absolute", left: 0, top: -scroll * k, width: VIEWPORT.w, height: im.h * k, opacity }} />;
  };
  const b = LAPTOP.bezel;
  return (
    <>
      {/* lid */}
      <div style={{ position: "absolute", left: LAPTOP.x - b, top: LAPTOP.y - b, width: LAPTOP.w + 2 * b, height: LAPTOP.h + 2 * b, borderRadius: 26,
        background: "linear-gradient(180deg, #1c1d21, #0d0e10)", boxShadow: "inset 0 0 0 2px #303238, 0 50px 90px -40px rgba(30,24,16,0.45)" }}>
        <div style={{ position: "absolute", top: 5, left: "50%", width: 5, height: 5, marginLeft: -2.5, borderRadius: "50%", background: "#26303d" }} />
      </div>
      {/* screen */}
      <div style={{ position: "absolute", left: LAPTOP.x, top: LAPTOP.y, width: LAPTOP.w, height: LAPTOP.h, borderRadius: 6, overflow: "hidden", background: "#fff" }}>
        <div style={{ height: LAPTOP.bar, background: "#f0f3f4", borderBottom: "1px solid #e3e6ea", position: "relative" }}>
          <div style={{ position: "absolute", left: 12, top: 9, display: "flex", gap: 6 }}>
            {LIGHTS.map((c) => <div key={c} style={{ width: 9, height: 9, borderRadius: "50%", background: c }} />)}
          </div>
          <div style={{ position: "absolute", left: "18.5%", width: "47.5%", top: 5, height: 18, borderRadius: 5, background: "#fff", border: "1px solid #e4e7eb",
            fontFamily: SANS, fontSize: 9.5, lineHeight: "17px", color: "#475467", textAlign: "center", whiteSpace: "nowrap", overflow: "hidden" }}>
            <svg width="7" height="8" viewBox="0 0 10 12" style={{ marginRight: 4, verticalAlign: "-0.5px" }}>
              <rect x="1" y="5" width="8" height="6.5" rx="1.4" fill={LOOK.muted} />
              <path d="M3 5.2V3.6a2 2 0 0 1 4 0v1.6" fill="none" stroke={LOOK.muted} strokeWidth="1.4" />
            </svg>
            {url}
          </div>
        </div>
        <div style={{ position: "absolute", left: 0, top: LAPTOP.bar, width: VIEWPORT.w, height: VIEWPORT.h, overflow: "hidden" }}>
          {page(img, 1)}
          {next && mix > 0 ? page(next, mix) : null}
        </div>
      </div>
      {/* base */}
      <div style={{ position: "absolute", left: LAPTOP.x - 115, top: LAPTOP.y + LAPTOP.h + b - 2, width: LAPTOP.w + 230, height: 20, borderRadius: "3px 3px 22px 22px",
        background: "linear-gradient(180deg, #e7e9ee 0%, #c9ccd3 55%, #a3a7af 100%)", boxShadow: "0 26px 40px -18px rgba(30,24,16,0.45)" }}>
        <div style={{ position: "absolute", left: "50%", top: 0, width: 190, marginLeft: -95, height: 8, borderRadius: "0 0 9px 9px", background: "linear-gradient(180deg, #b7bac1, #d5d8dd)" }} />
      </div>
    </>
  );
};

/** Laptop screenshot px → world px. */
export const laptopToWorld = (img: Img, scroll: number, x: number, y: number): [number, number] => {
  const k = VIEWPORT.w / img.w;
  return [VIEWPORT.x + x * k, VIEWPORT.y + (y - scroll) * k];
};
