import { continueRender, delayRender, staticFile } from "remotion";

const FACES: [string, string, FontFaceDescriptors][] = [
  ["Instrument Serif", "fonts/InstrumentSerif-Regular.ttf", { style: "normal" }],
  ["Instrument Serif", "fonts/InstrumentSerif-Italic.ttf", { style: "italic" }],
  ["Inter", "fonts/Inter-Variable.ttf", { weight: "100 900" }],
  ["Geist", "fonts/Geist-Variable.ttf", { weight: "100 900" }],
];

let started = false;

/** Load the house fonts once; rendering waits until they are ready. */
export const loadFonts = (): void => {
  if (started) {
    return;
  }
  started = true;
  const handle = delayRender("house fonts");
  Promise.all(
    FACES.map(([family, file, desc]) => {
      const face = new FontFace(family, `url(${staticFile(file)})`, desc);
      (document.fonts as unknown as { add: (f: FontFace) => void }).add(face);
      return face.load();
    }),
  ).then(
    () => continueRender(handle),
    (err: unknown) => {
      throw new Error(`house fonts failed to load: ${String(err)}`);
    },
  );
};
