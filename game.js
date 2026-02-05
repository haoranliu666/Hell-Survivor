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

const WEAPONS = {
  sword: {
    name: "Sword",
    color: "#ffd177",
  },
  bow: {
    name: "Bow",
    color: "#8fd6ff",
  },
  bomb: {
    name: "Bomb",
    color: "#ff9e72",
  },
};

const UPGRADES = [
  { id: "speed", label: "Speed Boost", color: "#8fffa8" },
  { id: "vitality", label: "Vitality", color: "#9ad8ff" },
  { id: "ironSword", label: "Iron Sword", color: "#ffd177" },
  { id: "multiArrow", label: "Multi Arrow", color: "#8fd6ff" },
  { id: "megaBomb", label: "Mega Bomb", color: "#ff9e72" },
];

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
    this.baseSpeed = 2.1;
    this.speedBoost = 0;

    this.facing = { x: 1, y: 0 };
    this.lastMove = { x: 1, y: 0 };

    this.weapon = null;
    this.swordLevel = 0;
    this.extraArrows = 0;
    this.bombLevel = 0;

    this.attackCooldown = 0;
    this.attackFrames = 0;
    this.shootCooldown = 0;
    this.bombCooldown = 0;

    this.isDodging = false;
    this.dodgeFrames = 0;
    this.dodgeCooldown = 0;
    this.dodgeVec = { x: 1, y: 0 };

    this.invFrames = 0;
    this.damageFlash = 0;

    this.exp = 0;
    this.level = 1;
    this.expPerLevel = 100;

    this.kills = 0;
  }

  get speed() {
    return this.baseSpeed + this.speedBoost;
  }

  get swordDamage() {
    return 2 + this.swordLevel + Math.floor(this.swordLevel / 2);
  }

  get bombDamage() {
    return 3 + this.bombLevel * 2;
  }

  get bombRange() {
    return 44 + this.bombLevel * 18;
  }

  get attackRange() {
    return 40 + this.swordLevel * 10;
  }

  update() {
    if (this.isDodging) {
      this.x += this.dodgeVec.x * 5.0;
      this.y += this.dodgeVec.y * 5.0;
      this.dodgeFrames -= 1;
      if (this.dodgeFrames <= 0) this.isDodging = false;
    } else {
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
        this.lastMove.x = dx;
        this.lastMove.y = dy;
        this.x += dx * this.speed;
        this.y += dy * this.speed;
      }
    }

    this.x = clamp(this.x, ISLAND.x + this.r, ISLAND.x + ISLAND.w - this.r);
    this.y = clamp(this.y, ISLAND.y + this.r, ISLAND.y + ISLAND.h - this.r);

    this.attackCooldown = Math.max(0, this.attackCooldown - 1);
    this.attackFrames = Math.max(0, this.attackFrames - 1);
    this.shootCooldown = Math.max(0, this.shootCooldown - 1);
    this.bombCooldown = Math.max(0, this.bombCooldown - 1);
    this.dodgeCooldown = Math.max(0, this.dodgeCooldown - 1);
    this.invFrames = Math.max(0, this.invFrames - 1);
    this.damageFlash = Math.max(0, this.damageFlash - 1);
  }

  usePrimary(game) {
    if (this.weapon === "sword") {
      if (this.attackCooldown > 0 || this.isDodging) return;
      this.attackCooldown = 16;
      this.attackFrames = 7;
      return;
    }

    if (this.weapon === "bow") {
      if (this.shootCooldown > 0 || this.isDodging) return;
      this.shootCooldown = 24;
      const dirs = this.getArrowDirections();
      for (const d of dirs) {
        game.projectiles.push({
          kind: "arrow",
          x: this.x,
          y: this.y,
          dx: d.x,
          dy: d.y,
          speed: 6.4,
          life: 120,
          damage: 1,
          r: 4,
        });
      }
      return;
    }

    if (this.weapon === "bomb") {
      if (this.bombCooldown > 0 || this.isDodging) return;
      this.bombCooldown = 88;
      const mv = Math.hypot(this.lastMove.x, this.lastMove.y) || 1;
      const dx = this.lastMove.x / mv;
      const dy = this.lastMove.y / mv;
      game.projectiles.push({
        kind: "bomb",
        x: this.x,
        y: this.y,
        dx,
        dy,
        speed: 4.2,
        life: 32,
        damage: this.bombDamage,
        range: this.bombRange,
        r: 7,
      });
    }
  }

  dodge() {
    if (this.dodgeCooldown > 0 || this.isDodging || this.attackFrames > 0) return;
    const mv = Math.hypot(this.lastMove.x, this.lastMove.y) || 1;
    this.dodgeVec.x = this.lastMove.x / mv;
    this.dodgeVec.y = this.lastMove.y / mv;
    this.isDodging = true;
    this.dodgeFrames = 12;
    this.dodgeCooldown = 45;
    this.invFrames = Math.max(this.invFrames, 12);
  }

  hurt(amount) {
    if (this.invFrames > 0 || this.isDodging) return;
    this.health = Math.max(0, this.health - amount);
    this.invFrames = 30;
    this.damageFlash = 10;
  }

  gainExp(amount) {
    this.exp += amount;
    while (this.exp >= this.expPerLevel) {
      this.exp -= this.expPerLevel;
      this.level += 1;
      this.expPerLevel = Math.round(this.expPerLevel * 1.15);
      this.maxHealth += 5;
      this.health = Math.min(this.maxHealth, this.health + 5);
      this.speedBoost += 0.05;
    }
  }

  applyUpgrade(upgradeId) {
    if (upgradeId === "speed") this.speedBoost += 0.15;
    if (upgradeId === "vitality") {
      this.maxHealth = 150;
      this.health = this.maxHealth;
    }
    if (upgradeId === "ironSword") this.swordLevel += 1;
    if (upgradeId === "multiArrow") this.extraArrows += 1;
    if (upgradeId === "megaBomb") this.bombLevel += 1;
  }

  getArrowDirections() {
    const dirs = [];
    const mv = Math.hypot(this.facing.x, this.facing.y) || 1;
    const base = { x: this.facing.x / mv, y: this.facing.y / mv };
    dirs.push(base);

    const spreadDeg = 15;
    const maxPairs = this.extraArrows;
    for (let i = 1; i <= maxPairs; i += 1) {
      const a = (spreadDeg * i * Math.PI) / 180;
      dirs.push(rotate(base, a));
      dirs.push(rotate(base, -a));
    }
    return dirs;
  }

  getAttackPoint() {
    return {
      x: this.x + this.facing.x * this.attackRange,
      y: this.y + this.facing.y * this.attackRange,
      r: 24 + this.swordLevel * 2,
    };
  }

  draw() {
    const fill = this.damageFlash ? "#f9d4c7" : "#e8d1bf";
    if (this.invFrames > 0 && Math.floor(this.invFrames / 4) % 2 === 0) ctx.globalAlpha = 0.55;

    ctx.fillStyle = fill;
    ctx.fillRect(this.x - 7, this.y - 10, 14, 20);
    ctx.fillStyle = "#2c1f25";
    ctx.fillRect(this.x - 8, this.y - 15, 16, 7);
    ctx.fillStyle = "#db5346";
    ctx.fillRect(this.x - 3, this.y - 13, 2, 2);
    ctx.fillRect(this.x + 1, this.y - 13, 2, 2);

    if (this.isDodging) {
      ctx.strokeStyle = "#8fd6ff";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(this.x, this.y, 16, 0, Math.PI * 2);
      ctx.stroke();
    }

    if (this.attackFrames > 0 && this.weapon === "sword") {
      const a = this.getAttackPoint();
      ctx.strokeStyle = "#ffd177";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(a.x, a.y, 18 + this.swordLevel * 2, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.globalAlpha = 1;
  }
}

class Enemy {
  constructor(type, x, y, wave = 1) {
    this.type = type;
    this.x = x;
    this.y = y;
    this.dead = false;
    this.hitFlash = 0;

    const waveScale = 1 + (wave - 1) * 0.1;

    if (type === "skeleton") {
      this.r = 11;
      this.speed = 1.0 + (wave - 1) * 0.03;
      this.hp = Math.max(1, Math.round(1 * waveScale));
      this.damage = 10;
      this.exp = 22;
      this.score = 10;
      this.color = "#ddd7ce";
    } else if (type === "ghost") {
      this.r = 10;
      this.speed = 0.8 + (wave - 1) * 0.03;
      this.hp = Math.max(1, Math.round(1 * waveScale));
      this.damage = 6;
      this.exp = 18;
      this.score = 8;
      this.color = "#b2bed9";
    } else {
      this.r = 30;
      this.speed = 0.85 + (wave - 1) * 0.02;
      this.hp = 7 + Math.floor((wave - 1) * 1.3);
      this.maxHp = this.hp;
      this.damage = 24;
      this.exp = 120;
      this.score = 120;
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
  projectiles: [],
  pickups: [],

  tick: 0,
  startedAt: 0,
  gameOver: false,
  won: false,
  awaitingWeaponChoice: true,

  currentWave: 1,
  waveKills: 0,
  waveStartTick: 0,
  waveActive: false,
  bossesRemaining: 0,

  score: 0,
  message: "",
  messageTimer: 0,

  highscores: [],
};

function rotate(v, angle) {
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  return { x: v.x * c - v.y * s, y: v.x * s + v.y * c };
}

function loadHighscores() {
  try {
    const raw = localStorage.getItem("hellSurvivorHighscores");
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed;
  } catch {
    return [];
  }
}

function saveHighscore() {
  const entry = {
    score: game.score,
    time: Math.floor((performance.now() - game.startedAt) / 1000),
    wave: game.currentWave,
    weapon: game.player.weapon ? WEAPONS[game.player.weapon].name : "None",
  };

  game.highscores.push(entry);
  game.highscores.sort((a, b) => b.score - a.score || b.wave - a.wave || b.time - a.time);
  game.highscores = game.highscores.slice(0, 10);
  localStorage.setItem("hellSurvivorHighscores", JSON.stringify(game.highscores));
}

function resetGame() {
  game.player.reset();
  game.enemies = [];
  game.food = [];
  game.particles = [];
  game.projectiles = [];
  game.pickups = [];

  game.tick = 0;
  game.startedAt = performance.now();
  game.gameOver = false;
  game.won = false;
  game.awaitingWeaponChoice = true;

  game.currentWave = 1;
  game.waveKills = 0;
  game.waveStartTick = 0;
  game.waveActive = false;
  game.bossesRemaining = 0;

  game.score = 0;
  game.message = "Choose your weapon: Sword / Bow / Bomb";
  game.messageTimer = 999999;

  game.highscores = loadHighscores();
  spawnWeaponPedestals();
}

function spawnWeaponPedestals() {
  const cx = GAME_W / 2;
  const cy = GAME_H / 2;
  game.pickups.push({ kind: "weapon", weapon: "sword", x: cx - 85, y: cy + 10, r: 10 });
  game.pickups.push({ kind: "weapon", weapon: "bow", x: cx, y: cy + 10, r: 10 });
  game.pickups.push({ kind: "weapon", weapon: "bomb", x: cx + 85, y: cy + 10, r: 10 });
}

function spawnEnemy() {
  if (game.gameOver || game.won || game.awaitingWeaponChoice) return;
  const maxEnemies = 10 + game.currentWave * 2;
  if (game.enemies.length >= maxEnemies) return;

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
  game.enemies.push(new Enemy(t, x, y, game.currentWave));
}

function spawnBoss() {
  game.waveActive = true;
  game.bossesRemaining = Math.min(1 + Math.floor((game.currentWave - 1) / 2), 3);
  for (let i = 0; i < game.bossesRemaining; i += 1) {
    game.enemies.push(new Enemy("boss", GAME_W / 2 + i * 45 - 45, ISLAND.y + 42, game.currentWave));
  }
  game.message = `Wave ${game.currentWave}: ${game.bossesRemaining} boss(es)!`;
  game.messageTimer = 120;
}

function completeWave() {
  game.waveActive = false;
  game.currentWave += 1;
  game.waveKills = 0;
  game.waveStartTick = game.tick;

  // drop one heart-like heal pickup
  game.food.push({
    x: clamp(GAME_W / 2 + rnd(-80, 80), ISLAND.x + 20, ISLAND.x + ISLAND.w - 20),
    y: clamp(GAME_H / 2 + rnd(-60, 60), ISLAND.y + 20, ISLAND.y + ISLAND.h - 20),
    r: 7,
    heal: 28,
  });

  const upgrade = UPGRADES[Math.floor(Math.random() * UPGRADES.length)];
  game.player.applyUpgrade(upgrade.id);
  game.message = `${upgrade.label} acquired!`;
  game.messageTimer = 150;
}

function checkWaveTrigger() {
  if (game.waveActive) return;
  const timeSinceWave = game.tick - game.waveStartTick;
  const timeTrigger = 60 * 60;
  const killTrigger = 10;
  if (timeSinceWave >= timeTrigger || game.waveKills >= killTrigger) {
    spawnBoss();
  }
}

function spawnFood() {
  if (game.food.length >= 8 || game.gameOver || game.won) return;
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

function updateProjectiles() {
  const pendingExplosions = [];

  for (const p of game.projectiles) {
    p.x += p.dx * p.speed;
    p.y += p.dy * p.speed;
    p.life -= 1;

    if (p.kind === "arrow") {
      for (const e of game.enemies) {
        if (e.dead) continue;
        const d2 = dist2(p.x, p.y, e.x, e.y);
        if (d2 < (p.r + e.r) ** 2) {
          e.hurt(e.type === "boss" ? p.damage : 999);
          p.life = 0;
          if (e.dead) handleEnemyDeath(e);
          break;
        }
      }
    }

    if (p.kind === "bomb") {
      if (p.life <= 0) {
        pendingExplosions.push({ x: p.x, y: p.y, range: p.range, damage: p.damage });
      }
    }
  }

  for (const ex of pendingExplosions) {
    spawnParticles(ex.x, ex.y, 45, "#ff9e72");
    for (const e of game.enemies) {
      if (e.dead) continue;
      const d2 = dist2(ex.x, ex.y, e.x, e.y);
      if (d2 < (ex.range + e.r) ** 2) {
        e.hurt(ex.damage);
        if (e.dead) handleEnemyDeath(e);
      }
    }
  }

  game.projectiles = game.projectiles.filter(
    (p) => p.life > 0 && p.x > -50 && p.x < GAME_W + 50 && p.y > -50 && p.y < GAME_H + 50,
  );
}

function handleEnemyDeath(enemy) {
  game.player.kills += 1;
  game.waveKills += 1;
  game.score += enemy.score;
  game.player.gainExp(enemy.exp);
  spawnParticles(enemy.x, enemy.y, enemy.type === "boss" ? 45 : 15, "#ffb56e");

  if (enemy.type === "boss") {
    game.bossesRemaining -= 1;
    game.message = `Boss down! ${Math.max(0, game.bossesRemaining)} remaining`;
    game.messageTimer = 90;
    if (game.bossesRemaining <= 0) {
      completeWave();
      if (game.currentWave > 6) {
        game.won = true;
      }
    }
  }
}

function updatePickups() {
  let lockedChoice = false;

  game.pickups = game.pickups.filter((p) => {
    const d2 = dist2(p.x, p.y, game.player.x, game.player.y);
    if (d2 < (p.r + game.player.r) ** 2) {
      if (p.kind === "weapon" && !game.player.weapon) {
        game.player.weapon = p.weapon;
        game.awaitingWeaponChoice = false;
        game.waveStartTick = game.tick;
        game.message = `${WEAPONS[p.weapon].name} chosen!`;
        game.messageTimer = 150;
        spawnParticles(p.x, p.y, 20, WEAPONS[p.weapon].color);
        lockedChoice = true;
      }
      return false;
    }
    return true;
  });

  if (lockedChoice) {
    game.pickups = game.pickups.filter((p) => p.kind !== "weapon");
  }
}


function update() {
  if (paused || game.gameOver || game.won) return;

  game.tick += 1;
  game.player.update();

  updatePickups();

  if (game.awaitingWeaponChoice) {
    if (game.messageTimer > 0) game.messageTimer -= 1;
    return;
  }

  const spawnInterval = Math.max(26, 55 - game.currentWave * 3);
  if (game.tick % spawnInterval === 0) spawnEnemy();
  if (game.tick % 240 === 0) spawnFood();

  checkWaveTrigger();

  for (const enemy of game.enemies) {
    enemy.update(game.player);

    const d2 = dist2(enemy.x, enemy.y, game.player.x, game.player.y);
    const touch = enemy.r + game.player.r;
    if (d2 < touch * touch && game.tick % 16 === 0) {
      game.player.hurt(enemy.damage);
    }
  }

  if (game.player.attackFrames > 0 && game.player.weapon === "sword") {
    const a = game.player.getAttackPoint();
    for (const enemy of game.enemies) {
      if (enemy.dead) continue;
      const d2 = dist2(a.x, a.y, enemy.x, enemy.y);
      const hitR = a.r + enemy.r;
      if (d2 < hitR * hitR) {
        enemy.hurt(enemy.type === "boss" ? game.player.swordDamage : game.player.swordDamage + 2);
        if (enemy.dead) handleEnemyDeath(enemy);
      }
    }
  }

  updateProjectiles();

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

  if (game.messageTimer > 0) game.messageTimer -= 1;

  if (game.player.health <= 0) {
    game.gameOver = true;
    saveHighscore();
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

function drawEntities() {
  // weapon pickups
  for (const p of game.pickups) {
    if (p.kind !== "weapon") continue;
    ctx.fillStyle = WEAPONS[p.weapon].color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "#1f1619";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r + 3, 0, Math.PI * 2);
    ctx.stroke();
  }

  // food
  ctx.fillStyle = "#9adb76";
  for (const f of game.food) {
    ctx.beginPath();
    ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
    ctx.fill();
  }

  // projectiles
  for (const p of game.projectiles) {
    if (p.kind === "arrow") {
      ctx.fillStyle = "#8fd6ff";
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillStyle = "#ff9e72";
      ctx.fillRect(p.x - 5, p.y - 5, 10, 10);
    }
  }

  for (const p of game.particles) {
    ctx.globalAlpha = Math.min(1, p.life / 20);
    ctx.fillStyle = p.color;
    ctx.fillRect(p.x, p.y, 3, 3);
  }
  ctx.globalAlpha = 1;

  for (const enemy of game.enemies) enemy.draw();
  game.player.draw();
}

function drawHud() {
  // panel
  ctx.fillStyle = "rgba(0,0,0,0.52)";
  ctx.fillRect(10, 10, 380, 104);

  // hp
  const hpPercent = game.player.health / game.player.maxHealth;
  ctx.fillStyle = "#311319";
  ctx.fillRect(20, 30, 180, 14);
  ctx.fillStyle = hpPercent > 0.4 ? "#67cc70" : "#ea5959";
  ctx.fillRect(20, 30, 180 * hpPercent, 14);

  // exp
  const expPercent = game.player.exp / game.player.expPerLevel;
  ctx.fillStyle = "#18253b";
  ctx.fillRect(20, 52, 180, 12);
  ctx.fillStyle = "#7dc8ff";
  ctx.fillRect(20, 52, 180 * expPercent, 12);

  ctx.fillStyle = "#f9ede8";
  ctx.font = "14px monospace";
  ctx.fillText(`HP: ${Math.ceil(game.player.health)}/${game.player.maxHealth}`, 210, 42);
  ctx.fillText(`LV: ${game.player.level} EXP ${game.player.exp}/${game.player.expPerLevel}`, 210, 62);

  const elapsed = Math.floor((performance.now() - game.startedAt) / 1000);
  const weaponName = game.player.weapon ? WEAPONS[game.player.weapon].name : "None";
  const weaponPlus =
    game.player.weapon === "sword"
      ? `+${game.player.swordLevel}`
      : game.player.weapon === "bow"
        ? `+${game.player.extraArrows}`
        : game.player.weapon === "bomb"
          ? `+${game.player.bombLevel}`
          : "";

  ctx.fillText(`Wave: ${game.currentWave}`, 20, 84);
  ctx.fillText(`Kills: ${game.player.kills}`, 105, 84);
  ctx.fillText(`Time: ${elapsed}s`, 190, 84);
  ctx.fillStyle = "#ffd177";
  ctx.fillText(`Score: ${game.score}`, 280, 84);

  ctx.fillStyle = "#f9ede8";
  ctx.fillText(`Weapon: ${weaponName}${weaponPlus}`, 20, 104);

  if (game.waveActive) {
    ctx.fillStyle = "#f2b4ad";
    ctx.fillText(`Bosses: ${game.bossesRemaining}`, 210, 104);
  } else {
    const timeToWave = Math.max(0, 60 - Math.floor((game.tick - game.waveStartTick) / 60));
    const killsToWave = Math.max(0, 10 - game.waveKills);
    ctx.fillStyle = "#ffa765";
    ctx.fillText(`Next wave: ${timeToWave}s / ${killsToWave} kills`, 180, 104);
  }

  // active boss bars
  const bosses = game.enemies.filter((e) => e.type === "boss");
  bosses.forEach((boss, i) => {
    const y = 10 + i * 24;
    ctx.fillStyle = "rgba(0,0,0,0.5)";
    ctx.fillRect(GAME_W - 250, y, 240, 20);
    ctx.fillStyle = "#3f1414";
    ctx.fillRect(GAME_W - 196, y + 4, 170, 10);
    ctx.fillStyle = "#d04c4c";
    ctx.fillRect(GAME_W - 196, y + 4, (boss.hp / boss.maxHp) * 170, 10);
    ctx.fillStyle = "#f2b4ad";
    ctx.fillText(`BOSS ${i + 1}`, GAME_W - 245, y + 14);
  });

  if (game.awaitingWeaponChoice) {
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.fillRect(GAME_W / 2 - 240, GAME_H / 2 - 110, 480, 86);
    ctx.fillStyle = "#ffe7d4";
    ctx.textAlign = "center";
    ctx.font = "bold 22px sans-serif";
    ctx.fillText("Choose Your Weapon", GAME_W / 2, GAME_H / 2 - 74);
    ctx.font = "15px sans-serif";
    ctx.fillText("Walk into Sword, Bow, or Bomb to lock your run.", GAME_W / 2, GAME_H / 2 - 46);
    ctx.textAlign = "left";
  }

  if (game.messageTimer > 0 && game.message) {
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.fillRect(GAME_W / 2 - 180, 18, 360, 30);
    ctx.fillStyle = "#ffe7d4";
    ctx.textAlign = "center";
    ctx.font = "bold 16px sans-serif";
    ctx.fillText(game.message, GAME_W / 2, 39);
    ctx.textAlign = "left";
  }

  if (paused) {
    drawCenteredText("PAUSED", "Press P to resume");
  }

  if (game.gameOver) {
    drawCenteredText("YOU DIED", "Press R to restart");
    drawHighscores();
  }

  if (game.won) {
    drawCenteredText("VICTORY!", "You cleared wave 6. Press R to play again.");
    drawHighscores();
  }
}

function drawHighscores() {
  ctx.fillStyle = "rgba(0,0,0,0.58)";
  ctx.fillRect(GAME_W / 2 - 250, GAME_H / 2 + 72, 500, 182);
  ctx.fillStyle = "#ffe7d4";
  ctx.textAlign = "center";
  ctx.font = "bold 18px sans-serif";
  ctx.fillText("Top 10 High Scores", GAME_W / 2, GAME_H / 2 + 98);

  ctx.font = "14px monospace";
  game.highscores.forEach((h, i) => {
    const line = `${i + 1}. ${h.score}pts  ${h.time}s  W${h.wave}  [${h.weapon}]`;
    ctx.fillStyle = i < 3 ? "#ffd177" : "#d9d4cf";
    ctx.fillText(line, GAME_W / 2, GAME_H / 2 + 122 + i * 14);
  });

  if (game.highscores.length === 0) {
    ctx.fillStyle = "#d9d4cf";
    ctx.fillText("No scores yet", GAME_W / 2, GAME_H / 2 + 125);
  }
  ctx.textAlign = "left";
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
  drawEntities();
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
    if (!game.gameOver && !game.won) game.player.usePrimary(game);
  }
  if (e.code === "ShiftLeft" || e.code === "ShiftRight") {
    if (!game.gameOver && !game.won) game.player.dodge();
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
loop();
