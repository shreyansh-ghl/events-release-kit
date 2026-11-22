/**
 * Pointing hand for phone taps and a macOS pointer for web clicks.
 * Ported from the Attendee App launch film (the team-approved look).
 */
interface FingerProps {
  x: number;
  y: number;
  press: number; // 0 hovering, 1 touching
  show: number; // 0..1
  scale?: number;
  angle?: number;
}

/** The fingertip sits exactly at (x, y); the hand extends down-right. */
export const Finger = ({ x, y, press, show, scale = 1, angle = -24 }: FingerProps) => {
  if (show <= 0.001) {
    return null;
  }
  const lift = 1 - press;
  const s = scale * (1 + lift * 0.05);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, pointerEvents: "none", opacity: show }}>
      {press > 0.05 ? (
        <div style={{ position: "absolute", left: -38 * scale, top: -38 * scale, width: 76 * scale, height: 76 * scale, borderRadius: "50%",
          background: `radial-gradient(circle, rgba(255,255,255,${0.55 * press}) 0%, rgba(255,255,255,0) 70%)` }} />
      ) : null}
      <div style={{ position: "absolute", left: 0, top: 0, transform: `translate(${lift * 10 * scale}px, ${lift * 16 * scale}px) rotate(${angle}deg) scale(${s})`, transformOrigin: "0 0" }}>
        <svg width={360} height={640} viewBox="-120 -14 360 640"
          style={{ position: "absolute", left: -120, top: -14, overflow: "visible",
            filter: `drop-shadow(${8 + lift * 18}px ${14 + lift * 26}px ${14 + lift * 18}px rgba(16,24,40,${0.28 - lift * 0.08}))` }}>
          <defs>
            <linearGradient id="skinX" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0" stopColor="#C98B68" />
              <stop offset="0.28" stopColor="#E9B896" />
              <stop offset="0.55" stopColor="#F3CCB0" />
              <stop offset="1" stopColor="#D49A78" />
            </linearGradient>
            <linearGradient id="skinPalm" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0" stopColor="#EDBF9F" />
              <stop offset="1" stopColor="#C88866" />
            </linearGradient>
          </defs>
          <path d="M 30 250 C 62 226 112 228 132 252 C 168 244 204 262 208 296 C 238 306 246 346 228 378 L 214 640 L -54 640 L -70 430 C -110 392 -118 338 -88 306 C -66 284 -46 300 -40 326 L -38 260 Z" fill="url(#skinPalm)" />
          <path d="M 132 252 C 140 280 138 300 128 318 M 208 296 C 212 320 208 340 196 356" stroke="#B9785A" strokeOpacity="0.45" strokeWidth="3" fill="none" />
          <path d="M -38 300 L -38 40 C -38 8 -18 -8 0 -8 C 18 -8 38 8 38 40 L 40 300 Z" fill="url(#skinX)" />
          <path d="M -20 32 C -20 12 -10 4 0 4 C 10 4 20 12 20 32 L 18 66 C 8 71 -8 71 -18 66 Z" fill="#F8DFCF" opacity="0.85" />
          <path d="M -20 32 C -20 12 -10 4 0 4 C 10 4 20 12 20 32" stroke="#E7BFA6" strokeWidth="2" fill="none" />
          <path d="M -26 138 C -10 132 10 132 26 138 M -28 222 C -10 216 12 216 30 222" stroke="#B9785A" strokeOpacity="0.4" strokeWidth="3" fill="none" />
        </svg>
      </div>
    </div>
  );
};

/** macOS-like pointer, drawn in frame space at a fixed size. */
export const Pointer = ({ x, y, press, show, scale = 1.25 }: { x: number; y: number; press: number; show: number; scale?: number }) => {
  if (show <= 0.001) {
    return null;
  }
  return (
    <div style={{ position: "absolute", left: x, top: y, pointerEvents: "none", opacity: show }}>
      {press > 0.02 ? (
        <div style={{ position: "absolute", left: -26 * scale, top: -26 * scale, width: 52 * scale, height: 52 * scale, borderRadius: "50%",
          background: `rgba(21,94,239,${0.22 * press})`, transform: `scale(${0.6 + press * 0.6})` }} />
      ) : null}
      <svg width={28 * scale} height={32 * scale} viewBox="0 0 26 30" style={{ transform: `scale(${1 - press * 0.12})`, transformOrigin: "2px 2px", filter: "drop-shadow(0 3px 4px rgba(0,0,0,0.3))" }}>
        <path d="M2 2 L2 24 L8 18.5 L12 27.5 L16 25.8 L12.2 17 L20 17 Z" fill="#101828" stroke="#fff" strokeWidth="2" strokeLinejoin="round" />
      </svg>
    </div>
  );
};
