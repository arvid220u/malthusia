import G from "./globals";
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
      current round: {round}. location: ({hover_coord[0]}, {hover_coord[1]})
    </div>
  );
}

export default ControlPane;
