import { useCallback, useRef, useEffect, useState } from "react";
import Map from "./Map";

function App() {
  return (
    <div class="h-screen w-screen flex flex-col">
      <h1 class="text-center text-lg font-bold">malthusia</h1>
      <Map />
    </div>
  );
}

export default App;
