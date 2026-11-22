/** HighLevel mark (three arrows), traced from the film's end card at 4K. viewBox = 260 x 232. */
const ARROWS: { c: string; shade: string; apex: number; top: number; stem: [number, number]; head: [number, number] }[] = [
  { c: "#ffbc00", shade: "#e9a512", apex: 55, top: 0, stem: [37, 73], head: [0, 109] },
  { c: "#188bf6", shade: "#0f72d6", apex: 131, top: 84, stem: [113, 149], head: [75, 186] },
  { c: "#37ca37", shade: "#24ac25", apex: 205.5, top: 0, stem: [188, 224], head: [151, 260] },
];

export const HighLevelMark = ({ height }: { height: number }) => (
  <svg width={(height * 260) / 232} height={height} viewBox="0 0 260 232">
    {ARROWS.map((a) => {
      const base = a.top + 56;
      return (
        <g key={a.c}>
          <rect x={a.stem[0]} y={base - 1} width={a.stem[1] - a.stem[0]} height={232 - base + 1} fill={a.c} />
          <polygon points={`${a.apex},${base} ${a.stem[1]},${base} ${a.stem[1]},${base + 20}`} fill={a.shade} />
          <polygon points={`${a.apex},${a.top} ${a.head[0]},${base} ${a.head[1]},${base}`} fill={a.c} />
        </g>
      );
    })}
  </svg>
);
