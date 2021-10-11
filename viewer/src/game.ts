import * as PIXI from "pixi.js";

// external graphics
const GRID_SIZE = 13;
const GRID_SPACING = 0;
const WATER_COLOR = 0x024b86;

const DIRT_COLORS: Map<number, Array<number>> = new Map<number, Array<number>>([
  [-5, [0, 147, 83]], // turquoise
  [3, [29, 201, 2]], // green
  [10, [254, 205, 54]], // yellow
  [90, [222, 145, 1]], // brown
  [500, [255, 0, 0]], // red
  [2000, [242, 0, 252]], // pink
]);

// internal graphics
const MAX_SPRITES_PER_TYPE = 1000;
const N_TYPES = 1;
const TYPE_NAME = ["WANDERER"];

type Game = {
  current_round: number;
  max_rounds: number;
  map_states: Location[][];
};
type Location = {
  x: number;
  y: number;
  elevation: number;
  water: boolean;
  robot: Robot | null;
  dead_robots: Robot[];
};
type Robot = {
  id: number;
  type: number;
  creator: string;
  x: number;
  y: number;
  alive: boolean;
};

export type Viewer = {
  grid: PIXI.Container;
  graphics: PIXI.Graphics;
  dyn_graphics: PIXI.Graphics;
  grid_overlay: PIXI.Graphics;
  unit_health: PIXI.Graphics;
  app: PIXI.Application;
  center_x: number;
  center_y: number;
  hover_coordinate: [number, number];
  spritepool: PIXI.Sprite[][];
  game: Game | null;
  last_turn_time: number | null;
  anim_frame: number | null;
  autoplay_delay: number;
  is_playing: boolean;
  render_callbacks: Array<() => void>;
};

export function setup_map(
  container: HTMLElement,
  render_callbacks: Array<() => void>
): Viewer {
  // On first render create our application
  const app = new PIXI.Application({
    resizeTo: container,
    resolution: devicePixelRatio,
    backgroundColor: 0x0,
  });

  // Add app to DOM
  container.appendChild(app.view);

  // Start the PixiJS app
  app.start();

  const center_x = app.renderer.width / (2 * devicePixelRatio);
  const center_y = app.renderer.height / (2 * devicePixelRatio);

  // grid container so we can zoom and move around
  const grid = new PIXI.Container();
  app.stage.addChild(grid);

  // initialize graphics object
  const background = new PIXI.Graphics();
  background.beginFill(WATER_COLOR);
  //   background.drawRect(-10000, -10000, 20000, 20000);
  background.drawCircle(center_x, center_y, 10000);
  background.endFill();
  grid.addChild(background);

  const dyn_graphics = new PIXI.Graphics();
  grid.addChild(dyn_graphics);

  const graphics = new PIXI.Graphics();
  grid.addChild(graphics);

  const grid_overlay = new PIXI.Graphics();
  grid.addChild(grid_overlay);

  const unit_health = new PIXI.Graphics();
  grid.addChild(unit_health);

  const viewer: Viewer = {
    grid,
    graphics,
    dyn_graphics,
    grid_overlay,
    unit_health,
    app,
    center_x,
    center_y,
    hover_coordinate: [-1, -1],
    spritepool: [],
    game: null,
    last_turn_time: null,
    anim_frame: null,
    autoplay_delay: 20,
    is_playing: false,
    render_callbacks,
  };

  // initialize textures
  const textures = Array(N_TYPES);
  // wanderer: geometrical design by Vectors Market from the Noun Project
  textures[0] = PIXI.Texture.from("/img/wanderer.png");

  // initialize a spritepool
  viewer.spritepool = Array(N_TYPES);
  for (var i = 0; i < N_TYPES; ++i) {
    viewer.spritepool[i] = [];

    for (var j = 0; j < MAX_SPRITES_PER_TYPE; ++j) {
      var sprite = new PIXI.Sprite(textures[i]);
      // sprite.anchor = new PIXI.ObservablePoint(0, 0);
      sprite.visible = false;
      grid.addChild(sprite);
      viewer.spritepool[i].push(sprite);
    }
  }

  // interactive graphic components
  app.ticker.add(function (delta) {
    var mouseposition = app.renderer.plugins.interaction.mouse.global;

    const [gx, gy] = screen_to_game_coordinates(
      viewer,
      (mouseposition.x - grid.position.x) / grid.scale.x,
      (mouseposition.y - grid.position.y) / grid.scale.y
    );

    if (
      gx !== viewer.hover_coordinate[0] ||
      gy !== viewer.hover_coordinate[1]
    ) {
      viewer.hover_coordinate = [gx, gy];
      render(viewer);
    }
  });

  // drag to move
  grid.interactive = true;

  let dragger: { select_point: any; dragging: boolean } = {
    select_point: null,
    dragging: false,
  };

  function start_drag(event) {
    dragger.select_point = event.data.getLocalPosition(grid.parent);

    dragger.select_point!.x -= grid.position.x;
    dragger.select_point!.y -= grid.position.y;

    dragger.dragging = true;
  }

  function end_drag() {
    dragger.dragging = false;
  }

  function do_drag(event) {
    if (dragger.dragging) {
      var newPosition = event.data.getLocalPosition(grid.parent);

      grid.position.x = newPosition.x - dragger.select_point!.x;
      grid.position.y = newPosition.y - dragger.select_point!.y;
    }
  }

  grid
    .on("mousedown", start_drag)
    .on("mouseup", end_drag)
    .on("mouseupoutside", end_drag)
    .on("mousemove", do_drag);

  // scroll to zoom
  container.addEventListener("wheel", function (event) {
    if (!event || !grid.transform) {
      return;
    }
    // calculate target position in the grid's coordinate frame
    var px = event.x - grid.position.x;
    var py = event.y - grid.position.y;

    var zoom_amount = Math.pow(3 / 4, event.deltaY / 120);

    grid.scale.x *= zoom_amount;
    grid.scale.y *= zoom_amount;

    grid.position.x -= px * (zoom_amount - 1);
    grid.position.y -= py * (zoom_amount - 1);
  });

  return viewer;
}

function render(viewer: Viewer) {
  // clear the graphics so we can redraw
  viewer.dyn_graphics.clear();
  viewer.grid_overlay.clear();
  viewer.unit_health.clear();

  // hover coordinate
  var x = viewer.hover_coordinate[0];
  var y = viewer.hover_coordinate[1];

  // draw selection box
  outline_square(viewer, 0x9e42f4, x, y);

  // TODO: only re-render changed things, instead of ALL things
  draw_grid(viewer);

  //   this.write_stats();
  //   this.write_tooltip();
  //   this.render_action();
  for (const cb of viewer.render_callbacks) {
    cb();
  }
}

function game_to_screen_coordinates(
  viewer: Viewer,
  x: number,
  y: number
): [number, number] {
  let gx = x * (GRID_SIZE + GRID_SPACING);
  let gy = y * (GRID_SIZE + GRID_SPACING);

  return [gx + viewer.center_x, viewer.center_y - gy];
}
function screen_to_game_coordinates(
  viewer: Viewer,
  gx: number,
  gy: number
): [number, number] {
  let x = Math.floor((gx - viewer.center_x) / (GRID_SIZE + GRID_SPACING));
  let y = Math.ceil((viewer.center_y - gy) / (GRID_SIZE + GRID_SPACING));

  return [x, y];
}

function dirt_color(x: number): number {
  /*
    I'm thinking the following:
    - A gradient following the rainbow of the following colors. Defined in cst.DIRT_COLORS
    */

  // // (-inf~inf) -> (0~1)
  // // TODO getting inputs for color transition?
  // const ex = Math.exp(x / 10);
  // const t = ex / (5 + ex);

  // iterate and find the two colors
  let lo: number[] = [0, 0, 0];
  let hi: number[] = [0, 0, 0];
  let mx: number = -1000;
  let mn: number = -1000;
  for (let entry of Array.from(DIRT_COLORS)) {
    lo = hi;
    hi = entry[1];
    mn = mx;
    mx = entry[0];
    if (x <= entry[0]) {
      break;
    }
  }
  if (mn === -1000) {
    lo = hi;
    mn = mx;
    mx += 1;
  }

  // convert into range and truncate
  let t = (x - mn) / (mx - mn);
  if (x <= mn) {
    t = 0;
  }
  if (x >= mx) {
    t = 1;
  }

  let now = [0, 0, 0];
  for (let i = 0; i < 3; i++) now[i] = Math.round((hi[i] - lo[i]) * t + lo[i]);

  let hx = now[0] * 0x10000 + now[1] * 0x100 + now[2];
  return hx;
}

function outline_square(viewer: Viewer, color, x: number, y: number) {
  viewer.grid_overlay.beginFill(color, 0.2);
  const [gx, gy] = game_to_screen_coordinates(viewer, x, y);
  viewer.grid_overlay.drawRect(
    gx - GRID_SPACING,
    gy - GRID_SPACING,
    GRID_SIZE + 2 * GRID_SPACING,
    GRID_SIZE + 2 * GRID_SPACING
  );
  viewer.grid_overlay.endFill();
}

function render_autoplay_frame(viewer: Viewer, curr_time) {
  if (viewer.last_turn_time == null) {
    viewer.last_turn_time = curr_time;
    viewer.anim_frame = requestAnimationFrame((x) =>
      render_autoplay_frame(viewer, x)
    );
    return;
  }

  var num_turns_elapsed = Math.ceil(
    Math.max(curr_time - viewer.last_turn_time, 0) / viewer.autoplay_delay
  );
  viewer.last_turn_time += num_turns_elapsed * viewer.autoplay_delay;
  viewer.game!.current_round = Math.min(
    viewer.game!.current_round + num_turns_elapsed,
    viewer.game!.max_rounds - 1
  );
  render(viewer);

  if (viewer.game!.current_round < viewer.game!.max_rounds - 1) {
    viewer.anim_frame = requestAnimationFrame((x) =>
      render_autoplay_frame(viewer, x)
    );
  } else {
    stop_autoplay(viewer);
  }
}

export function start_autoplay(viewer: Viewer) {
  if (!viewer.game) return;
  if (viewer.is_playing) return;
  viewer.is_playing = true;

  // disable manual buttons
  //   document.getElementById("btn_next_turn").classList.add("disabled");
  //   document.getElementById("btn_prev_turn").classList.add("disabled");
  //   document.getElementById("btn_next_round").classList.add("disabled");
  //   document.getElementById("btn_prev_round").classList.add("disabled");
  //   document.getElementById("btn_next_robin").classList.add("disabled");
  //   document.getElementById("btn_prev_robin").classList.add("disabled");

  //   // disable slider inputs
  //   document.getElementById("input_range_set_turn").disabled = true;
  //   document.getElementById("input_range_set_round").disabled = true;

  //   // configure start/stop
  //   document.getElementById("btn_start_autoplay").classList.add("disabled");
  //   document.getElementById("btn_stop_autoplay").classList.remove("disabled");
  //   document.getElementById("btn_jump_start").classList.add("disabled");

  // Simple function to play at arbitrary speed
  viewer.last_turn_time = null;
  viewer.anim_frame = requestAnimationFrame((x) =>
    render_autoplay_frame(viewer, x)
  );
}

function stop_autoplay(viewer: Viewer) {
  if (!viewer.is_playing) return;
  viewer.is_playing = false;

  if (viewer.anim_frame) {
    cancelAnimationFrame(viewer.anim_frame);
  }

  // enable manual buttons
  //   document.getElementById("btn_next_turn").classList.remove("disabled");
  //   document.getElementById("btn_prev_turn").classList.remove("disabled");
  //   document.getElementById("btn_next_round").classList.remove("disabled");
  //   document.getElementById("btn_prev_round").classList.remove("disabled");
  //   document.getElementById("btn_next_robin").classList.remove("disabled");
  //   document.getElementById("btn_prev_robin").classList.remove("disabled");

  //   // enable slider inputs
  //   document.getElementById("input_range_set_turn").disabled = false;
  //   document.getElementById("input_range_set_round").disabled = false;

  //   // configure start/stop
  //   document.getElementById("btn_start_autoplay").classList.remove("disabled");
  //   document.getElementById("btn_stop_autoplay").classList.add("disabled");
  //   document.getElementById("btn_jump_start").classList.remove("disabled");
}

export function draw_grid(viewer: Viewer) {
  if (!viewer.game) {
    return;
  }
  viewer.graphics.clear();

  // hide all units
  for (let i = 0; i < N_TYPES; ++i) {
    for (let j = 0; j < MAX_SPRITES_PER_TYPE; ++j) {
      viewer.spritepool[i][j].visible = false;
    }
  }

  var sprite_index = Array(N_TYPES);
  for (let i = 0; i < N_TYPES; ++i) sprite_index[i] = 0;

  // render tiles
  for (const location of viewer.game.map_states[viewer.game.current_round]) {
    // determine tile color
    if (location.water) {
      viewer.graphics.beginFill(WATER_COLOR);
    } else {
      viewer.graphics.beginFill(dirt_color(location.elevation));
    }
    // calculate grid position
    const [gx, gy] = game_to_screen_coordinates(viewer, location.x, location.y);

    const robot = location.robot;
    if (robot) {
      // check if we have enough sprites
      if (sprite_index[robot.type] >= MAX_SPRITES_PER_TYPE) {
        throw Error(
          "Ran out of sprites! Increase MAX_SPRITES_PER_TYPE and try again..."
        );
      }

      var sprite = viewer.spritepool[robot.type][sprite_index[robot.type]];
      sprite_index[robot.type]++;

      // set up the sprite
      sprite.visible = true;
      sprite.width = GRID_SIZE;
      sprite.height = GRID_SIZE;
      sprite.position.x = gx;
      sprite.position.y = gy;
      sprite.tint = 0xff0000;
    }

    // draw it
    viewer.graphics.drawRect(gx, gy, GRID_SIZE, GRID_SIZE);
    viewer.graphics.endFill();
  }
}

// load replay
// TODO: add FROM index here!! so that we can get state of the world from a particular round on.
export async function load_replay() {
  console.log("loading_replay");
  // const resp = await fetch('/replay')
  const url = process.env.REACT_APP_API_URL + "/replay";
  const resp = await fetch(url);
  if (resp.ok) {
    const data = await resp.json();
    return process_replay(data);
  } else {
    console.error("no replay file");
  }
}

function process_replay(replay: any) {
  console.log("process");
  console.log(replay);

  const game: Game = {
    current_round: 0,
    map_states: replay,
    max_rounds: replay.length,
  };

  return game;
}
