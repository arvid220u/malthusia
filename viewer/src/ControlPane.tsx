import G from "./globals";
import { start_autoplay } from "./game";
import { useEffect, useState } from "react";

function ControlPane() {
  const [round, setRound] = useState(0);
  const [hover_coord, setHoverCoord] = useState([0, 0]);
  useEffect(() => {
    G.render_callbacks.push(() =>
      setRound(G.viewer?.game ? G.viewer.game.current_round : 0)
    );
    G.render_callbacks.push(() =>
      setHoverCoord(G.viewer ? G.viewer.hover_coordinate : [0, 0])
    );
  }, []);
  return (
    <div className="p-1">
      <button
        onClick={() => G.viewer && start_autoplay(G.viewer)}
        className="bg-blue-500 hover:bg-blue-700 text-white px-4 rounded"
      >
        start autoplay!
      </button>{" "}
      current round: {round}. location: ({hover_coord[0]}, {hover_coord[1]})
    </div>
  );
}

export default ControlPane;
