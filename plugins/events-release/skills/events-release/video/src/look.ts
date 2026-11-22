/** House look for video (mirrors tokens.json). Product UI is never drawn here: screens are captured. */
export const LOOK = {
  paper: "#eeeae3",
  paperHi: "#f6f3ee",
  paperLo: "#e2ddd4",
  ink: "#1b1a16",
  inkHi: "#26231f",
  inkText: "#171512",
  nightText: "#f3efe7",
  nightMuted: "rgba(243,239,231,0.62)",
  muted: "#6d665c",
  blue: "#1a89f1",
  amber: "#f9b803",
  green: "#37ca37",
};

export const SERIF = "'Instrument Serif', serif";
export const SANS = "'Inter', sans-serif";
export const LABEL = "'Geist', sans-serif";

export const PAPER_BG = `radial-gradient(85% 75% at 50% 30%, ${LOOK.paperHi} 0%, ${LOOK.paper} 55%, ${LOOK.paperLo} 100%)`;
export const NIGHT_BG = `radial-gradient(70% 70% at 50% 45%, ${LOOK.inkHi} 0%, ${LOOK.ink} 70%, #141310 100%)`;
