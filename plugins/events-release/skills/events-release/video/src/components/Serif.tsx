import { CSSProperties, Fragment } from "react";
import { SERIF } from "../look";

/** Serif headline: "*phrase*" is the one italic emphasis, "\n" a deliberate line break. */
export const Serif = ({ text, style }: { text: string; style?: CSSProperties }) => (
  <div style={{ fontFamily: SERIF, fontWeight: 400, letterSpacing: "-0.012em", lineHeight: 1, ...style }}>
    {text.split("\n").map((line, i) => (
      <Fragment key={i}>
        {i ? <br /> : null}
        {line.split(/(\*[^*]+\*)/).filter(Boolean).map((part, j) =>
          part.startsWith("*") && part.endsWith("*") ? <em key={j} style={{ fontStyle: "italic" }}>{part.slice(1, -1)}</em> : <Fragment key={j}>{part}</Fragment>,
        )}
      </Fragment>
    ))}
  </div>
);
