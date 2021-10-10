import { useCallback, useRef, useEffect, useState } from "react";
import * as PIXI from "pixi.js";
import { setup_map, load_replay, draw_grid } from "./game";

function Map() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // On first render create our application
    const app = new PIXI.Application({
      resizeTo: ref.current!,
      resolution: devicePixelRatio,
      backgroundColor: 0xffaaaa,
    });

    // Add app to DOM
    ref.current!.appendChild(app.view);

    // Start the PixiJS app
    app.start();

    const viewer = setup_map(app, ref.current!);
    load_replay().then(function(game) {
      if (game) {
        draw_grid(game, viewer);
      }
    })

    return () => {
      // On unload completely destroy the application and all of it's children
      app.destroy(true, true);
    };
  }, []);

  return <div ref={ref} className="flex flex-grow flex-shrink h-40"></div>;
}

export default Map;
