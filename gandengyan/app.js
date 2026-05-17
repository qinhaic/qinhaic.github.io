const RANKS = ["3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "2"];
const SUITS = [
  { symbol: "♠", red: false },
  { symbol: "♥", red: true },
  { symbol: "♣", red: false },
  { symbol: "♦", red: true },
];
const NPC_NAMES = ["小美", "阿土", "莉莉"];

const state = {
  seats: 2,
  players: [],
  scores: [100, 100],
  deck: [],
  turn: 0,
  leader: 0,
  current: null,
  passCount: 0,
  round: 1,
  lastWinner: null,
  selected: new Set(),
  locked: false,
  showNpcHands: false,
  exited: false,
  started: false,
  nextRoundTimer: null,
};

const saved = JSON.parse(localStorage.getItem("gdy-settings") || "{}");
if (Number.isInteger(saved.seats) && saved.seats >= 2 && saved.seats <= 4) {
  state.seats = saved.seats;
}
if (Number.isInteger(saved.lastWinner) && saved.lastWinner >= 0 && saved.lastWinner < state.seats) {
  state.lastWinner = saved.lastWinner;
  state.round = Math.max(2, Number(saved.round) || 2);
}
if (Array.isArray(saved.scores) && saved.scores.length === state.seats) {
  state.scores = saved.scores.map((score) => Number(score) || 0);
} else {
  state.scores = Array.from({ length: state.seats }, () => 100);
}
state.showNpcHands = Boolean(saved.showNpcHands);

const el = {
  opponents: document.querySelector("#opponents"),
  deckCount: document.querySelector("#deckCount"),
  currentPlay: document.querySelector("#currentPlay"),
  currentMeta: document.querySelector("#currentMeta"),
  turnName: document.querySelector("#turnName"),
  message: document.querySelector("#message"),
  hand: document.querySelector("#hand"),
  playBtn: document.querySelector("#playBtn"),
  passBtn: document.querySelector("#passBtn"),
  newGameBtn: document.querySelector("#newGameBtn"),
  exitBtn: document.querySelector("#exitBtn"),
  startScreen: document.querySelector("#startScreen"),
  startChoices: document.querySelectorAll(".start-choice"),
  showNpcHands: document.querySelector("#showNpcHands"),
  roundText: document.querySelector("#roundText"),
  selectionHint: document.querySelector("#selectionHint"),
  seatChoices: document.querySelectorAll(".seat-choice"),
  scoreboard: document.querySelector("#scoreboard"),
};

function makeDeck() {
  const deck = [];
  let id = 1;
  for (const rank of RANKS) {
    for (const suit of SUITS) {
      deck.push({
        id: `c${id++}`,
        rank,
        value: RANKS.indexOf(rank),
        suit: suit.symbol,
        red: suit.red,
        joker: false,
      });
    }
  }
  deck.push({ id: `c${id++}`, rank: "小王", value: null, suit: "★", red: true, joker: true });
  deck.push({ id: `c${id++}`, rank: "大王", value: null, suit: "★", red: false, joker: true });
  return shuffle(deck);
}

function shuffle(cards) {
  const copy = cards.slice();
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function sortCards(cards) {
  return cards.slice().sort((a, b) => {
    if (a.joker && b.joker) return a.rank.localeCompare(b.rank, "zh-CN");
    if (a.joker) return 1;
    if (b.joker) return -1;
    if (a.value !== b.value) return a.value - b.value;
    return a.suit.localeCompare(b.suit);
  });
}

function startGame() {
  clearNextRoundTimer();
  state.exited = false;
  state.started = true;
  el.startScreen.classList.add("hidden");
  ensureScores();
  if (state.lastWinner !== null && state.lastWinner >= state.seats) {
    state.lastWinner = null;
    state.round = 1;
  }
  state.players = Array.from({ length: state.seats }, (_, index) => ({
    name: index === 0 ? "你" : NPC_NAMES[index - 1],
    hand: [],
    human: index === 0,
    playedThisRound: false,
  }));
  state.deck = makeDeck();
  state.current = null;
  state.passCount = 0;
  state.selected.clear();
  state.locked = false;

  for (let i = 0; i < 5; i += 1) {
    for (const player of state.players) {
      player.hand.push(state.deck.pop());
    }
  }

  state.turn = state.lastWinner ?? Math.floor(Math.random() * state.players.length);
  state.leader = state.turn;
  drawOne(state.turn);
  state.players.forEach((player) => {
    player.hand = sortCards(player.hand);
  });

  const opener = state.players[state.turn].name;
  setMessage(`${opener}先手，已多摸一张。`);
  render();
  maybeNpcTurn();
}

function drawOne(playerIndex) {
  if (state.deck.length > 0) {
    state.players[playerIndex].hand.push(state.deck.pop());
    state.players[playerIndex].hand = sortCards(state.players[playerIndex].hand);
  }
}

function countRanks(cards) {
  const counts = Array(RANKS.length).fill(0);
  let jokers = 0;
  for (const card of cards) {
    if (card.joker) jokers += 1;
    else counts[card.value] += 1;
  }
  return { counts, jokers };
}

function getCombos(cards) {
  const sorted = sortCards(cards);
  const { counts, jokers } = countRanks(sorted);
  const len = sorted.length;
  const combos = [];
  const realRanks = counts.map((count, value) => ({ count, value })).filter((item) => item.count > 0);

  if (len === 1 && !sorted[0].joker) {
    combos.push({ type: "single", rank: sorted[0].value, length: 1, cards: sorted });
  }

  if (len === 2) {
    for (let rank = 0; rank < RANKS.length; rank += 1) {
      if (counts[rank] > 0 && counts[rank] + jokers === 2 && realRanks.every((r) => r.value === rank)) {
        combos.push({ type: "pair", rank, length: 2, cards: sorted });
      }
    }
  }

  if (len === 3 || len === 4) {
    for (let rank = 0; rank < RANKS.length; rank += 1) {
      if (counts[rank] > 0 && counts[rank] + jokers === len && realRanks.every((r) => r.value === rank)) {
        combos.push({ type: "bomb", rank, bombSize: len, length: len, cards: sorted });
      }
    }
  }

  if (len >= 3) {
    for (let start = 0; start <= RANKS.length - len; start += 1) {
      const end = start + len - 1;
      const inWindow = realRanks.every((r) => r.value >= start && r.value <= end && r.count === 1);
      if (inWindow && realRanks.length + jokers === len) {
        combos.push({ type: "straight", start, end, rank: end, length: len, cards: sorted });
      }
    }
  }

  if (len >= 4 && len % 2 === 0) {
    const pairs = len / 2;
    for (let start = 0; start <= RANKS.length - pairs; start += 1) {
      const end = start + pairs - 1;
      const inWindow = realRanks.every((r) => r.value >= start && r.value <= end && r.count <= 2);
      if (!inWindow) continue;
      let missing = 0;
      for (let rank = start; rank <= end; rank += 1) {
        missing += 2 - counts[rank];
      }
      if (missing === jokers) {
        combos.push({ type: "consecutivePairs", start, end, rank: end, length: len, pairs, cards: sorted });
      }
    }
  }

  return combos;
}

function comboLabel(combo) {
  if (!combo) return "自由开牌";
  const labelByType = {
    single: "单张",
    pair: "对子",
    straight: "顺子",
    consecutivePairs: "连对",
    bomb: combo.bombSize === 4 ? "四张炸弹" : "三张炸弹",
  };
  if (combo.type === "straight") return `${labelByType[combo.type]} ${RANKS[combo.start]}-${RANKS[combo.end]}`;
  if (combo.type === "consecutivePairs") return `${labelByType[combo.type]} ${RANKS[combo.start]}-${RANKS[combo.end]}`;
  return `${labelByType[combo.type]} ${RANKS[combo.rank]}`;
}

function canBeat(candidate, current) {
  if (!current) return true;
  if (candidate.type === "bomb") {
    if (current.type !== "bomb") return true;
    if (candidate.bombSize !== current.bombSize) return candidate.bombSize > current.bombSize;
    return candidate.rank > current.rank;
  }
  if (current.type === "bomb") return false;
  if (candidate.type !== current.type || candidate.length !== current.length) return false;

  if (candidate.type === "single" || candidate.type === "pair") {
    if (candidate.rank === 12 && current.rank !== 12) return true;
    return candidate.rank === current.rank + 1;
  }

  if (candidate.type === "straight" || candidate.type === "consecutivePairs") {
    return candidate.start === current.start + 1;
  }

  return false;
}

function bestPlayableCombo(cards, current) {
  return getCombos(cards)
    .filter((combo) => canBeat(combo, current))
    .sort((a, b) => comboPower(a) - comboPower(b))[0] ?? null;
}

function comboPower(combo) {
  if (combo.type === "bomb") return 1000 + combo.bombSize * 100 + combo.rank;
  return combo.rank + combo.length * 0.01;
}

function nextPlayer(index) {
  return (index + 1) % state.players.length;
}

function removeCards(player, cards) {
  const ids = new Set(cards.map((card) => card.id));
  player.hand = player.hand.filter((card) => !ids.has(card.id));
}

function playCards(playerIndex, cards, combo) {
  const player = state.players[playerIndex];
  player.playedThisRound = true;
  removeCards(player, cards);
  state.current = { ...combo, cards: sortCards(cards), playerIndex };
  state.leader = playerIndex;
  state.passCount = 0;
  state.selected.clear();
  setMessage(`${player.name}出了${comboLabel(combo)}。`);

  if (player.hand.length === 0) {
    finishGame(playerIndex);
    return;
  }

  state.turn = nextPlayer(playerIndex);
  render();
  maybeNpcTurn();
}

function passTurn(playerIndex) {
  const player = state.players[playerIndex];
  state.passCount += 1;
  setMessage(`${player.name}不要。`);

  if (state.passCount >= state.players.length - 1) {
    endTrick();
    return;
  }

  state.turn = nextPlayer(playerIndex);
  render();
  maybeNpcTurn();
}

function endTrick() {
  const leader = state.leader;
  drawOne(leader);
  state.current = null;
  state.passCount = 0;
  state.turn = leader;
  setMessage(`${state.players[leader].name}赢得本轮，${state.deck.length > 0 ? "摸一张后" : "牌堆已空，"}继续开牌。`);
  render();
  maybeNpcTurn();
}

function finishGame(winnerIndex) {
  const settlement = settleScores(winnerIndex);
  state.lastWinner = winnerIndex;
  state.locked = true;
  state.round += 1;
  saveSettings();
  setMessage(`${state.players[winnerIndex].name}出完手牌，赢了这一局。${settlement} 下一局马上开始。`);
  render();
  state.nextRoundTimer = window.setTimeout(() => {
    if (!state.exited) startGame();
  }, 1600);
}

function settleScores(winnerIndex) {
  const parts = [];
  let winnerGain = 0;
  state.players.forEach((player, index) => {
    if (index === winnerIndex) return;
    const base = player.hand.length;
    const penalty = player.playedThisRound ? base : base * 2;
    state.scores[index] = Math.max(0, state.scores[index] - penalty);
    winnerGain += penalty;
    parts.push(`${player.name}扣${penalty}分`);
  });
  state.scores[winnerIndex] += winnerGain;
  if (winnerGain > 0) parts.push(`${state.players[winnerIndex].name}加${winnerGain}分`);
  return parts.join("，");
}

function ensureScores() {
  if (!Array.isArray(state.scores) || state.scores.length !== state.seats) {
    state.scores = Array.from({ length: state.seats }, () => 100);
  }
}

function exitGame() {
  clearNextRoundTimer();
  state.exited = true;
  state.locked = true;
  state.selected.clear();
  setMessage("已退出。点“新开一局”可以继续。");
  render();
}

function showStartScreen() {
  clearNextRoundTimer();
  state.started = false;
  state.exited = true;
  state.locked = true;
  state.selected.clear();
  el.startScreen.classList.remove("hidden");
  setMessage("请选择几家玩。");
  render();
}

function clearNextRoundTimer() {
  if (state.nextRoundTimer) {
    window.clearTimeout(state.nextRoundTimer);
    state.nextRoundTimer = null;
  }
}

function saveSettings() {
  localStorage.setItem(
    "gdy-settings",
    JSON.stringify({
      seats: state.seats,
      lastWinner: state.lastWinner,
      round: state.round,
      scores: state.scores,
      showNpcHands: state.showNpcHands,
    }),
  );
}

function chooseNpcMove(player) {
  const hand = player.hand;
  const candidates = [];
  for (let mask = 1; mask < 1 << hand.length; mask += 1) {
    const cards = [];
    for (let i = 0; i < hand.length; i += 1) {
      if (mask & (1 << i)) cards.push(hand[i]);
    }
    const combo = bestPlayableCombo(cards, state.current);
    if (combo) candidates.push({ cards, combo });
  }
  candidates.sort((a, b) => comboPower(a.combo) - comboPower(b.combo) || a.cards.length - b.cards.length);

  if (!state.current) return candidates.find((item) => item.combo.type !== "bomb") ?? candidates[0] ?? null;
  const nonBomb = candidates.find((item) => item.combo.type !== "bomb");
  if (nonBomb) return nonBomb;

  const canFinish = candidates.find((item) => item.cards.length === hand.length);
  if (canFinish) return canFinish;
  return null;
}

function maybeNpcTurn() {
  if (state.locked || state.players[state.turn].human) {
    render();
    return;
  }
  window.setTimeout(() => {
    if (state.locked || state.players[state.turn].human) return;
    const player = state.players[state.turn];
    const move = chooseNpcMove(player);
    if (move) playCards(state.turn, move.cards, move.combo);
    else passTurn(state.turn);
  }, 650);
}

function selectedCards() {
  const player = state.players[0];
  return player.hand.filter((card) => state.selected.has(card.id));
}

function handlePlay() {
  if (state.locked || state.turn !== 0) return;
  const cards = selectedCards();
  const combo = bestPlayableCombo(cards, state.current);
  if (!combo) {
    setMessage("这手牌不合法，或者压不上当前牌。");
    render();
    return;
  }
  playCards(0, cards, combo);
}

function handlePass() {
  if (state.locked || state.turn !== 0 || !state.current) return;
  passTurn(0);
}

function render() {
  renderScores();
  renderOpponents();
  renderCenter();
  renderHand();
  renderControls();
}

function renderScores() {
  el.scoreboard.innerHTML = "";
  state.players.forEach((player, index) => {
    const item = document.createElement("div");
    item.className = `score ${state.turn === index ? "active" : ""}`;
    item.innerHTML = `<span>${player.name}</span><strong>${state.scores[index]}分</strong>`;
    el.scoreboard.appendChild(item);
  });
}

function renderOpponents() {
  el.opponents.innerHTML = "";
  state.players.slice(1).forEach((player, offset) => {
    const index = offset + 1;
    const seat = document.createElement("div");
    seat.className = `seat ${state.turn === index ? "active" : ""}`;
    const backs = Array.from({ length: Math.min(player.hand.length, 5) }, () => `<span class="mini-back"></span>`).join("");
    const cards = sortCards(player.hand).map(cardHtml).join("");
    seat.innerHTML = `
      <div>
        <strong>${player.name}</strong>
        <small>${player.hand.length} 张手牌</small>
      </div>
      <div class="${state.showNpcHands ? "npc-faceup" : "back-cards"}">${state.showNpcHands ? cards : backs}</div>
    `;
    el.opponents.appendChild(seat);
  });
}

function renderCenter() {
  el.deckCount.textContent = state.deck.length;
  el.turnName.textContent = state.players[state.turn]?.name ?? "你";
  el.roundText.textContent = state.lastWinner === null ? "第一局随机先手" : `第${state.round}局，上局赢家先手`;

  if (!state.current) {
    el.currentPlay.className = "played-cards empty";
    el.currentPlay.textContent = "等待开牌";
    el.currentMeta.textContent = "领先者可以出任意合法牌型";
    return;
  }

  el.currentPlay.className = "played-cards";
  el.currentPlay.innerHTML = state.current.cards.map(cardHtml).join("");
  el.currentMeta.textContent = `${state.players[state.current.playerIndex].name}：${comboLabel(state.current)}`;
}

function renderHand() {
  const player = state.players[0];
  el.hand.innerHTML = "";
  for (const card of player.hand) {
    const button = document.createElement("button");
    button.className = cardClass(card, state.selected.has(card.id));
    button.innerHTML = cardInner(card);
    button.disabled = state.locked || state.turn !== 0;
    button.addEventListener("click", () => {
      if (state.selected.has(card.id)) state.selected.delete(card.id);
      else state.selected.add(card.id);
      render();
    });
    el.hand.appendChild(button);
  }

  const cards = selectedCards();
  const combo = cards.length ? bestPlayableCombo(cards, state.current) : null;
  el.selectionHint.textContent = combo ? `已选：${comboLabel(combo)}` : cards.length ? "已选牌暂时不能出" : "点牌选择，再出牌";
}

function renderControls() {
  const humanTurn = state.turn === 0 && !state.locked;
  const cards = selectedCards();
  const combo = cards.length ? bestPlayableCombo(cards, state.current) : null;
  el.playBtn.disabled = !humanTurn || !combo;
  el.passBtn.disabled = !humanTurn || !state.current;
}

function setMessage(text) {
  el.message.textContent = text;
}

function cardClass(card, selected = false) {
  return ["card", card.red ? "red" : "", card.joker ? "joker" : "", selected ? "selected" : ""].filter(Boolean).join(" ");
}

function cardInner(card) {
  return `
    <span class="rank">${card.rank}</span>
    <span class="suit">${card.suit}</span>
    <span class="corner">${card.suit}</span>
  `;
}

function cardHtml(card) {
  return `<span class="${cardClass(card)}">${cardInner(card)}</span>`;
}

window.__gdyRules = {
  ranks: RANKS,
  getCombos,
  bestPlayableCombo,
  canBeat,
};

el.playBtn.addEventListener("click", handlePlay);
el.passBtn.addEventListener("click", handlePass);
el.newGameBtn.addEventListener("click", showStartScreen);
el.exitBtn.addEventListener("click", exitGame);
el.showNpcHands.addEventListener("change", () => {
  state.showNpcHands = el.showNpcHands.checked;
  saveSettings();
  render();
});
el.seatChoices.forEach((button) => {
  button.addEventListener("click", () => {
    state.seats = Number(button.dataset.seats);
    el.seatChoices.forEach((choice) => choice.classList.toggle("active", choice === button));
    if (state.lastWinner !== null && state.lastWinner >= state.seats) {
      state.lastWinner = null;
      state.round = 1;
    }
    state.scores = Array.from({ length: state.seats }, () => 100);
    saveSettings();
    startGame();
  });
});
el.startChoices.forEach((button) => {
  button.addEventListener("click", () => {
    state.seats = Number(button.dataset.seats);
    state.lastWinner = null;
    state.round = 1;
    state.scores = Array.from({ length: state.seats }, () => 100);
    el.seatChoices.forEach((choice) => choice.classList.toggle("active", Number(choice.dataset.seats) === state.seats));
    saveSettings();
    startGame();
  });
});

el.seatChoices.forEach((choice) => choice.classList.toggle("active", Number(choice.dataset.seats) === state.seats));
el.showNpcHands.checked = state.showNpcHands;
showStartScreen();
