import { useCallback, useRef, useEffect, useState } from "react";
import * as PIXI from "pixi.js";

function Map() {
  const ref = useRef(null);

  useEffect(() => {
    // On first render create our application
    const app = new PIXI.Application({
      resizeTo: ref.current,
      backgroundColor: 0xffaaaa,
    });

    // Add app to DOM
    ref.current.appendChild(app.view);

    // Start the PixiJS app
    app.start();

    return () => {
      // On unload completely destroy the application and all of it's children
      app.destroy(true, true);
    };
  }, []);

  return <div ref={ref} class="flex flex-grow flex-shrink h-40"></div>;
}

export default Map;
