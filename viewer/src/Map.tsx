import { useCallback, useRef, useEffect, useState } from "react";
import { setup_map, load_replay, process_rounds } from "./game";
import G from "./globals";

function Map() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    G.viewer = setup_map(ref.current!, G.render_callbacks);
    const round_processer = process_rounds(G.viewer!);
    load_replay(round_processer);

    return () => {
      // On unload completely destroy the application and all of it's children
      G.viewer!.app.destroy(true, true);
    };
  }, []);

  return <div ref={ref} className="flex flex-grow flex-shrink h-40"></div>;
}

export default Map;
