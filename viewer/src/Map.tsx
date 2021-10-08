import { useCallback, useRef, useEffect, useState } from "react";
import * as PIXI from "pixi.js";
import { setup_map } from "./game";

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

    setup_map(app, {size: 40}, ref.current!)

    return () => {
      // On unload completely destroy the application and all of it's children
      app.destroy(true, true);
    };
  }, []);

  return <div ref={ref} className="flex flex-grow flex-shrink h-40"></div>;
}

export default Map;
