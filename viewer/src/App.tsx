import { useCallback, useRef, useEffect, useState } from "react";
import Map from "./Map";
import ControlPane from "./ControlPane";
import { RouteComponentProps } from "@gatsbyjs/reach-router";

function App(props: RouteComponentProps) {
  return (
    <div className="h-screen w-screen flex flex-col">
      <h1 className="text-center text-lg font-bold">malthusia</h1>
      <ControlPane />
      <Map />
    </div>
  );
}

export default App;
