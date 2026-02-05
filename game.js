const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const GAME_W = canvas.width;
const GAME_H = canvas.height;
const ISLAND_MARGIN = 36;
const ISLAND = {
  x: ISLAND_MARGIN,
  y: ISLAND_MARGIN,
  w: GAME_W - ISLAND_MARGIN * 2,
  h: GAME_H - ISLAND_MARGIN * 2,
};

const keys = new Set();
let paused = false;

const rnd = (min, max) => min + Math.random() * (max - min);
const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const dist2 = (ax, ay, bx, by) => {
  const dx = ax - bx;
  const dy = ay - by;
  return dx * dx + dy * dy;
};

class Player {
  constructor() {
    this.reset();
  }

  reset() {
    this.x = GAME_W / 2;
    this.y = GAME_H / 2;
    this.r = 10;
    this.maxHealth = 100;
    this.health = 100;
    this.speed = 2.15;
    this.attackCooldown = 0;
    this.attackFrames = 0;
    this.attackRange = 40;
    this.damageFlash = 0;
    this.facing = { x: 1, y: 0 };
    this.kills = 0;
  }

  update() {
    let dx = 0;
    let dy = 0;
    if (keys.has("KeyW") || keys.has("ArrowUp")) dy -= 1;
    if (keys.has("KeyS") || keys.has("ArrowDown")) dy += 1;
    if (keys.has("KeyA") || keys.has("ArrowLeft")) dx -= 1;
    if (keys.has("KeyD") || keys.has("ArrowRight")) dx += 1;

    if (dx !== 0 || dy !== 0) {
      const mag = Math.hypot(dx, dy);
      dx /= mag;
      dy /= mag;
      this.facing.x = dx;
      this.facing.y = dy;
      this.x += dx * this.speed;
      this.y += dy * this.speed;
    }

    this.x = clamp(this.x, ISLAND.x + this.r, ISLAND.x + ISLAND.w - this.r);
    this.y = clamp(this.y, ISLAND.y + this.r, ISLAND.y + ISLAND.h - this.r);

    this.attackCooldown = Math.max(0, this.attackCooldown - 1);
    this.attackFrames = Math.max(0, this.attackFrames - 1);
    this.damageFlash = Math.max(0, this.damageFlash - 1);
  }

  attack() {
    if (this.attackCooldown > 0) return;
    this.attackCooldown = 18;
    this.attackFrames = 7;
  }

  hurt(dmg) {
    this.health = Math.max(0, this.health - dmg);
    this.damageFlash = 10;
  }

  getAttackPoint() {
    return {
      x: this.x + this.facing.x * this.attackRange,
      y: this.y + this.facing.y * this.attackRange,
      r: 24,
    };
  }

  draw() {
    const fill = this.damageFlash ? "#f9d4c7" : "#e8d1bf";
    ctx.fillStyle = fill;
    ctx.fillRect(this.x - 7, this.y - 10, 14, 20);
    ctx.fillStyle = "#2c1f25";
    ctx.fillRect(this.x - 8, this.y - 15, 16, 7);
    ctx.fillStyle = "#db5346";
    ctx.fillRect(this.x - 3, this.y - 13, 2, 2);
    ctx.fillRect(this.x + 1, this.y - 13, 2, 2);

    if (this.attackFrames > 0) {
      const a = this.getAttackPoint();
      ctx.strokeStyle = "#ffd177";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(a.x, a.y, 18, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
}

class Enemy {
  constructor(type, x, y) {
    this.type = type;
    this.x = x;
    this.y = y;
    this.dead = false;
    this.hitFlash = 0;

    if (type === "skeleton") {
      this.r = 11;
      this.speed = 1.0;
      this.hp = 1;
      this.damage = 10;
      this.color = "#ddd7ce";
    } else if (type === "ghost") {
      this.r = 10;
      this.speed = 0.8;
      this.hp = 1;
      this.damage = 6;
      this.color = "#b2bed9";
    } else {
      this.r = 28;
      this.speed = 0.8;
      this.hp = 12;
      this.damage = 22;
      this.color = "#ad3939";
    }
  }

  update(player) {
    const dx = player.x - this.x;
    const dy = player.y - this.y;
    const mag = Math.hypot(dx, dy) || 1;
    this.x += (dx / mag) * this.speed;
    this.y += (dy / mag) * this.speed;
    this.hitFlash = Math.max(0, this.hitFlash - 1);
  }

  hurt(amount) {
    this.hp -= amount;
    this.hitFlash = 8;
    if (this.hp <= 0) this.dead = true;
  }

  draw() {
    ctx.fillStyle = this.hitFlash ? "#fff2ad" : this.color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#2f1d1d";
    ctx.beginPath();
    ctx.arc(this.x - 4, this.y - 3, 2, 0, Math.PI * 2);
    ctx.arc(this.x + 4, this.y - 3, 2, 0, Math.PI * 2);
    ctx.fill();
  }
}

const game = {
  player: new Player(),
  enemies: [],
  food: [],
  particles: [],
  tick: 0,
  gameOver: false,
  won: false,
  bossSpawned: false,
};

function resetGame() {
  game.player.reset();
  game.enemies = [];
  game.food = [];
  game.particles = [];
  game.tick = 0;
  game.gameOver = false;
  game.won = false;
  game.bossSpawned = false;
}

function spawnEnemy() {
  if (game.gameOver || game.won) return;
  if (game.enemies.length >= 15) return;

  const edge = Math.floor(Math.random() * 4);
  let x = 0;
  let y = 0;
  if (edge === 0) {
    x = rnd(ISLAND.x, ISLAND.x + ISLAND.w);
    y = ISLAND.y + 8;
  } else if (edge === 1) {
    x = ISLAND.x + ISLAND.w - 8;
    y = rnd(ISLAND.y, ISLAND.y + ISLAND.h);
  } else if (edge === 2) {
    x = rnd(ISLAND.x, ISLAND.x + ISLAND.w);
    y = ISLAND.y + ISLAND.h - 8;
  } else {
    x = ISLAND.x + 8;
    y = rnd(ISLAND.y, ISLAND.y + ISLAND.h);
  }

  const t = Math.random() < 0.5 ? "ghost" : "skeleton";
  game.enemies.push(new Enemy(t, x, y));
}

function spawnBoss() {
  game.bossSpawned = true;
  game.enemies.push(new Enemy("boss", GAME_W / 2, ISLAND.y + 40));
}

function spawnFood() {
  if (game.food.length >= 7 || game.gameOver || game.won) return;
  game.food.push({
    x: rnd(ISLAND.x + 20, ISLAND.x + ISLAND.w - 20),
    y: rnd(ISLAND.y + 20, ISLAND.y + ISLAND.h - 20),
    r: 6,
    heal: 18,
  });
}

function spawnParticles(x, y, count, color) {
  for (let i = 0; i < count; i += 1) {
    game.particles.push({
      x,
      y,
      dx: rnd(-1.6, 1.6),
      dy: rnd(-1.6, 1.6),
      life: rnd(10, 28),
      color,
    });
  }
}

function update() {
  if (paused || game.gameOver || game.won) return;

  game.tick += 1;
  game.player.update();

  if (game.tick % 55 === 0) spawnEnemy();
  if (game.tick % 240 === 0) spawnFood();

  if (!game.bossSpawned && (game.tick > 60 * 60 || game.player.kills >= 18)) {
    spawnBoss();
  }

  for (const enemy of game.enemies) {
    enemy.update(game.player);

    const d2 = dist2(enemy.x, enemy.y, game.player.x, game.player.y);
    const touch = enemy.r + game.player.r;
    if (d2 < touch * touch && game.tick % 20 === 0) {
      game.player.hurt(enemy.damage);
    }
  }

  if (game.player.attackFrames > 0) {
    const a = game.player.getAttackPoint();
    for (const enemy of game.enemies) {
      if (enemy.dead) continue;
      const d2 = dist2(a.x, a.y, enemy.x, enemy.y);
      const hitR = a.r + enemy.r;
      if (d2 < hitR * hitR) {
        enemy.hurt(enemy.type === "boss" ? 1 : 2);
        if (enemy.dead) {
          game.player.kills += 1;
          spawnParticles(enemy.x, enemy.y, enemy.type === "boss" ? 40 : 15, "#ffb56e");
          if (enemy.type === "boss") game.won = true;
        }
      }
    }
  }

  game.enemies = game.enemies.filter((e) => !e.dead);

  game.food = game.food.filter((f) => {
    const d2 = dist2(f.x, f.y, game.player.x, game.player.y);
    if (d2 < (f.r + game.player.r) ** 2) {
      game.player.health = Math.min(game.player.maxHealth, game.player.health + f.heal);
      spawnParticles(f.x, f.y, 10, "#9be37f");
      return false;
    }
    return true;
  });

  for (const p of game.particles) {
    p.x += p.dx;
    p.y += p.dy;
    p.life -= 1;
  }
  game.particles = game.particles.filter((p) => p.life > 0);

  if (game.player.health <= 0) {
    game.gameOver = true;
  }
}

function drawBackground() {
  const g = ctx.createLinearGradient(0, 0, 0, GAME_H);
  g.addColorStop(0, "#3d1515");
  g.addColorStop(1, "#200f12");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, GAME_W, GAME_H);

  ctx.fillStyle = "#742715";
  for (let i = 0; i < 70; i += 1) {
    const x = (i * 123 + game.tick * 0.7) % (GAME_W + 40);
    const y = (i * 71) % GAME_H;
    ctx.globalAlpha = 0.09;
    ctx.fillRect(x - 20, y, 40, 3);
  }
  ctx.globalAlpha = 1;

  ctx.fillStyle = "#5b494b";
  ctx.fillRect(ISLAND.x, ISLAND.y, ISLAND.w, ISLAND.h);
  ctx.strokeStyle = "#887173";
  ctx.lineWidth = 4;
  ctx.strokeRect(ISLAND.x, ISLAND.y, ISLAND.w, ISLAND.h);

  for (let i = 0; i < 10; i += 1) {
    ctx.globalAlpha = 0.08;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, i * 4 + ((game.tick / 2) % 4), GAME_W, 1);
  }
  ctx.globalAlpha = 1;
}

function drawHud() {
  const hpPercent = game.player.health / game.player.maxHealth;
  ctx.fillStyle = "rgba(0,0,0,0.5)";
  ctx.fillRect(10, 10, 230, 52);

  ctx.fillStyle = "#311319";
  ctx.fillRect(20, 30, 180, 16);
  ctx.fillStyle = hpPercent > 0.4 ? "#67cc70" : "#ea5959";
  ctx.fillRect(20, 30, 180 * hpPercent, 16);

  ctx.fillStyle = "#f9ede8";
  ctx.font = "14px monospace";
  ctx.fillText(`HP: ${Math.ceil(game.player.health)}`, 20, 23);
  ctx.fillText(`Kills: ${game.player.kills}`, 20, 57);

  if (game.bossSpawned && !game.won) {
    const boss = game.enemies.find((e) => e.type === "boss");
    if (boss) {
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      ctx.fillRect(GAME_W - 260, 10, 250, 36);
      ctx.fillStyle = "#f2b4ad";
      ctx.fillText("BOSS", GAME_W - 250, 24);
      ctx.fillStyle = "#3f1414";
      ctx.fillRect(GAME_W - 196, 16, 170, 14);
      ctx.fillStyle = "#d04c4c";
      ctx.fillRect(GAME_W - 196, 16, (boss.hp / 12) * 170, 14);
    }
  }

  if (paused) {
    drawCenteredText("PAUSED", "Press P to resume");
  }

  if (game.gameOver) {
    drawCenteredText("YOU DIED", "Press R to restart");
  }
  if (game.won) {
    drawCenteredText("VICTORY!", "Boss defeated. Press R to play again.");
  }
}

function drawCenteredText(title, subtitle) {
  ctx.fillStyle = "rgba(0,0,0,0.58)";
  ctx.fillRect(GAME_W / 2 - 205, GAME_H / 2 - 62, 410, 124);
  ctx.fillStyle = "#ffe7d4";
  ctx.textAlign = "center";
  ctx.font = "bold 30px sans-serif";
  ctx.fillText(title, GAME_W / 2, GAME_H / 2 - 8);
  ctx.font = "16px sans-serif";
  ctx.fillText(subtitle, GAME_W / 2, GAME_H / 2 + 28);
  ctx.textAlign = "left";
}

function draw() {
  drawBackground();

  ctx.fillStyle = "#9adb76";
  for (const f of game.food) {
    ctx.beginPath();
    ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
    ctx.fill();
  }

  for (const p of game.particles) {
    ctx.globalAlpha = Math.min(1, p.life / 20);
    ctx.fillStyle = p.color;
    ctx.fillRect(p.x, p.y, 3, 3);
  }
  ctx.globalAlpha = 1;

  for (const enemy of game.enemies) enemy.draw();
  game.player.draw();

  drawHud();
}

function loop() {
  update();
  draw();
  requestAnimationFrame(loop);
}

document.addEventListener("keydown", (e) => {
  keys.add(e.code);

  if (e.code === "Space") {
    e.preventDefault();
    if (!game.gameOver && !game.won) game.player.attack();
  }
  if (e.code === "KeyR") {
    resetGame();
  }
  if (e.code === "KeyP") {
    paused = !paused;
  }
});

document.addEventListener("keyup", (e) => {
  keys.delete(e.code);
});

resetGame();
spawnEnemy();
spawnEnemy();
loop();
