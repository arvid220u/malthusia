import * as PIXI from "pixi.js";

// external graphics
const GRID_SIZE = 13;
const GRID_SPACING = 1;
const WATER_COLOR = 0x0000ff;

// internal graphics
const MAX_SPRITES_PER_TYPE = 1000;

type Game = {
    current_round: number,
    map: Location[],
}
type Location = {
    x: number,
    y: number,
    elevation: number,
    water: boolean,
    robot: Robot | null,
    dead_robots: Robot[],
}
type Robot = {
    id: number,
    type: string,
    creator: string,
    x: number,
    y: number,
    alive: boolean
}

type Viewer = {
    graphics: PIXI.Graphics
}

export function setup_map(app, container): Viewer {
    // grid container so we can zoom and move around
    const grid = new PIXI.Container();
    app.stage.addChild(grid);

    // initialize graphics object
    const background = new PIXI.Graphics();
    background.beginFill(WATER_COLOR);
    background.drawRect(-10000,-10000,20000,20000);
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

    // initialize textures
    const textures = Array(6);
    textures[0] = PIXI.Texture.from('/img/castle.png');
    textures[1] = PIXI.Texture.from('/img/church.png');
    textures[2] = PIXI.Texture.from('/img/pilgrim.png');
    textures[3] = PIXI.Texture.from('/img/crusader.png');
    textures[4] = PIXI.Texture.from('/img/prophet.png');
    textures[5] = PIXI.Texture.from('/img/preacher.png');

    // initialize a spritepool
    const spritepool = Array(6);
    for (var i = 0; i < 6; ++i) {
        spritepool[i] = [];

        for (var j = 0; j < MAX_SPRITES_PER_TYPE; ++j) {
            var sprite = new PIXI.Sprite(textures[i]);
            // sprite.anchor = new PIXI.ObservablePoint(0, 0);
            sprite.visible = false;
            grid.addChild(sprite);
            spritepool[i].push(sprite);
        }
    }

    // interactive graphic components
    // const hover_coordinate = [-1,-1];
    // const selected_unit = -1; //index

    // set up interactive components
    // app.ticker.add(function(delta) {
    //     var mouseposition = app.renderer.plugins.interaction.mouse.global;

    //     // figure out what grid coordinate this is
    //     var gx = Math.floor((mouseposition.x - grid.position.x) / (GRID_SIZE + GRID_SPACING) / grid.scale.x);
    //     var gy = Math.floor((mouseposition.y - grid.position.y) / (GRID_SIZE + GRID_SPACING) / grid.scale.x);

    //     if (gx != hover_coordinate[0] || gy != hover_coordinate[1]) {
    //         hover_coordinate = [gx, gy];
    //         render();
    //     }
    // }.bind(grid, hover_coordinate));

    // drag to move
    grid.interactive = true;

    let dragger: {select_point: any, dragging: boolean} = {select_point: null, dragging: false}

    function start_drag(event){
        dragger.select_point = event.data.getLocalPosition(grid.parent);

        dragger.select_point!.x -= grid.position.x;
        dragger.select_point!.y -= grid.position.y;

        dragger.dragging = true;
    }

    function end_drag(){
        dragger.dragging = false;
    }

    function do_drag(event){
        if (dragger.dragging) {
            var newPosition = event.data.getLocalPosition(grid.parent);

            grid.position.x = newPosition.x - dragger.select_point!.x;
            grid.position.y = newPosition.y - dragger.select_point!.y;
        }
    }

    grid.on('mousedown', start_drag)
        .on('mouseup', end_drag)
        .on('mouseupoutside', end_drag)
        .on('mousemove', do_drag);

    // scroll to zoom
    container.addEventListener('wheel', function(event) {
        // calculate target position in the grid's coordinate frame
        var px = event.x - grid.position.x;
        var py = event.y - grid.position.y;

        var zoom_amount = Math.pow(3/4, event.deltaY / 120);

        grid.scale.x *= zoom_amount;
        grid.scale.y *= zoom_amount;

        grid.position.x -= (px * (zoom_amount - 1));
        grid.position.y -= (py * (zoom_amount - 1));
    });

    return {
        graphics
    }
}

export function draw_grid(game: Game, viewer: Viewer) {
    viewer.graphics.clear();

    // render tiles
    for (const location of game.map) {
        // determine tile color
        viewer.graphics.beginFill(0x111111);

        // calculate grid position
        var gx = location.x * (GRID_SIZE + GRID_SPACING);
        var gy = location.y * (GRID_SIZE + GRID_SPACING);

        // draw it
        viewer.graphics.drawRect(gx,gy,GRID_SIZE,GRID_SIZE);
        viewer.graphics.endFill();

    }
}

// load replay
// TODO: add FROM index here!! so that we can get state of the world from a particular round on.
export async function load_replay() {
    console.log('loading_replay')
    const resp = await fetch('/replay')
    if (resp.ok) {
        const data = await resp.json();
        return process_replay(data);
    } else {
        console.error('no replay file');
    }
}


function process_replay(replay: any) {
    console.log('process');

    const seed = 0;

    let game: Game = {
        current_round: 0,
        map: replay
    };

    return game;
}