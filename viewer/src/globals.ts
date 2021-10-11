import { Viewer } from "./game";

const G: { viewer: Viewer | null; render_callbacks: Array<() => void> } = {
  viewer: null,
  render_callbacks: [],
};
export default G;
