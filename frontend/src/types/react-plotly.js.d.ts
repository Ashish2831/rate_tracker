/** Plotly.js typings for react-plotly.js. */
declare module "react-plotly.js" {
  import type { CSSProperties, FC } from "react";
  import type { Config, Data, Layout } from "plotly.js";

  export interface PlotParams {
    data: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    style?: CSSProperties;
    useResizeHandler?: boolean;
  }

  const Plot: FC<PlotParams>;
  export default Plot;
}
