import { useCallback, useRef, useEffect, useState } from "react";
import { setup_map, load_replay, draw_grid } from "./game";
import G from "./globals";

function Map() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    G.viewer = setup_map(ref.current!, G.render_callbacks);
    load_replay().then(function (game) {
      if (game) {
        G.viewer!.game = game;
        draw_grid(G.viewer!);
      }
    });

    return () => {
      // On unload completely destroy the application and all of it's children
      G.viewer!.app.destroy(true, true);
    };
  }, []);

  return <div ref={ref} className="flex flex-grow flex-shrink h-40"></div>;
}

export default Map;
