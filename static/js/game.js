/**
 * Knightfall Chess - Main Game Logic
 * Handles WebSocket communication, board rendering, and user interactions
 */

class KnightfallGame {
  constructor() {
    this.socket = null;
    this.username = null;
    this.sessionId = null;
    this.gameId = null;
    this.playerColor = null;
    this.gameState = null;
    this.selectedSquare = null;
    this.moveHistory = [];

    // Initialize
    this.init();
  }

  init() {
    // Connect to server
    this.connectToServer();

    // Setup UI event listeners
    this.setupUIEventListeners();

    // Load saved themes
    const savedTheme = BoardThemes.loadSavedTheme();
    document.getElementById("theme-select").value = savedTheme;
    const savedVictoryTheme = localStorage.getItem("victoryTheme") || "anime";
    const victorySelect = document.getElementById("victory-theme-select");
    if (victorySelect) victorySelect.value = savedVictoryTheme;

    // Preload all victory GIFs into browser cache so they play instantly
    this.preloadVictoryGifs();
  }

  preloadVictoryGifs() {
    const allGifs = [
      "/static/images/anime/victory1.gif",
      "/static/images/anime/draw.gif",
      "/static/images/anime/victory3.gif",
      "/static/images/anime/loser.gif",
      "/static/images/harry_potter/hp1.gif",
      "/static/images/harry_potter/hp2.gif",
      "/static/images/harry_potter/hp3.gif",
      "/static/images/harry_potter/hp4.gif",
    ];
    allGifs.forEach((src) => {
      const img = new Image();
      img.src = src;
    });
  }

  connectToServer() {
    console.log("[Client] Connecting to server...");
    this.socket = io();

    // Connection events
    this.socket.on("connected", (data) => {
      console.log("[Client] Connected:", data.session_id);
      this.sessionId = data.session_id;
    });

    this.socket.on("disconnect", () => {
      console.log("[Client] Disconnected from server");
      this.showMessage("Disconnected from server", "error");
    });

    // Registration events
    this.socket.on("registered", (data) => {
      console.log("[Client] Registered:", data.username);
      this.username = data.username;
      document.getElementById("player-name").textContent = data.username;
      document.getElementById("player-elo").textContent = data.elo;
      this.showScreen("lobby");
    });

    // Matchmaking events
    this.socket.on("waiting_for_opponent", (data) => {
      console.log("[Client] Waiting for opponent...");
      document.getElementById("lobby-status").textContent = data.message;
      document.getElementById("find-game-btn").style.display = "none";
      document.getElementById("cancel-search-btn").style.display =
        "inline-block";
    });

    this.socket.on("search_cancelled", (data) => {
      console.log("[Client] Search cancelled");
      document.getElementById("lobby-status").textContent = "";
      document.getElementById("find-game-btn").style.display = "inline-block";
      document.getElementById("cancel-search-btn").style.display = "none";
    });

    this.socket.on("game_started", (data) => {
      console.log("[Client] Game started!", data);
      this.gameId = data.game_id;
      this.playerColor = data.color;
      this.gameState = data.game_state;
      this.moveHistory = [];

      this.showScreen("game");
      this.renderBoard();
      this.updateGameInfo();
      this.showMessage(`Game started! You are ${this.playerColor}`, "success");
    });

    // Game events
    this.socket.on("move_made", (data) => {
      console.log("[Client] Move made:", data);

      // Capture old ELOs before updating game state
      const oldWhiteElo = this.gameState ? this.gameState.white_elo : null;
      const oldBlackElo = this.gameState ? this.gameState.black_elo : null;

      // Update game state based on player color
      this.gameState =
        this.playerColor === "white"
          ? data.game_state_white
          : data.game_state_black;

      // Add to move history
      this.addMoveToHistory(data.from, data.to, data.player);

      // Re-render board
      this.renderBoard();
      this.updateGameInfo();

      // Clear selection
      this.selectedSquare = null;

      // Check for game over
      if (data.game_over) {
        const resolvedOldWhite = data.old_white_elo ?? oldWhiteElo;
        const resolvedOldBlack = data.old_black_elo ?? oldBlackElo;
        this.handleGameOver(
          data.winner,
          resolvedOldWhite,
          resolvedOldBlack,
          data.wager_payout,
        );
      }
    });

    this.socket.on("move_rejected", (data) => {
      console.log("[Client] Move rejected:", data.error);
      this.showMessage(`Invalid move: ${data.error}`, "error");
      this.selectedSquare = null;
      this.renderBoard();
    });

    // game_ended fires for resign and disconnect forfeit (no move involved)
    this.socket.on("game_ended", (data) => {
      console.log("[Client] Game ended:", data);
      const oldWhiteElo = data.old_white_elo ?? this.gameState?.white_elo;
      const oldBlackElo = data.old_black_elo ?? this.gameState?.black_elo;
      const gs =
        this.playerColor === "white"
          ? data.game_state_white
          : data.game_state_black;
      if (gs) {
        this.gameState = gs;
        this.renderBoard();
        this.updateGameInfo();
      }
      this.handleGameOver(
        data.winner,
        oldWhiteElo,
        oldBlackElo,
        data.wager_payout,
      );
    });

    this.socket.on("opponent_disconnected", (data) => {
      console.log("[Client] Opponent disconnected");
      this.showMessage(data.message, "error");
      setTimeout(() => {
        this.showScreen("lobby");
      }, 3000);
    });

    // Error handling
    this.socket.on("error", (data) => {
      console.error("[Client] Error:", data.message);
      this.showMessage(data.message, "error");
    });
  }

  setupUIEventListeners() {
    // Login
    document.getElementById("login-btn").addEventListener("click", () => {
      const username = document.getElementById("username-input").value.trim();
      if (username) {
        this.register(username);
      } else {
        alert("Please enter a username");
      }
    });

    document
      .getElementById("username-input")
      .addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          document.getElementById("login-btn").click();
        }
      });

    // Wallet
    this.setupWalletListeners();

    // Matchmaking
    document.getElementById("find-game-btn").addEventListener("click", () => {
      this.findGame();
    });

    document
      .getElementById("cancel-search-btn")
      .addEventListener("click", () => {
        this.cancelSearch();
      });

    // Theme selection
    document.getElementById("theme-select").addEventListener("change", (e) => {
      const theme = e.target.value;
      const board = document.getElementById("chess-board");
      BoardThemes.applyTheme(theme, board);
    });

    // Victory theme selection
    const victorySelect = document.getElementById("victory-theme-select");
    if (victorySelect) {
      victorySelect.addEventListener("change", (e) => {
        localStorage.setItem("victoryTheme", e.target.value);
      });
    }

    // Game controls
    document.getElementById("resign-btn").addEventListener("click", () => {
      if (confirm("Are you sure you want to resign?")) {
        this.resign();
      }
    });

    document.getElementById("new-game-btn").addEventListener("click", () => {
      this.showScreen("lobby");
      document.getElementById("new-game-btn").style.display = "none";
      document.getElementById("resign-btn").style.display = "inline-block";
    });
  }

  // ─── Wallet ──────────────────────────────────────────────────────────────

  setupWalletListeners() {
    const connectBtn = document.getElementById("connect-wallet-btn");
    const disconnectBtn = document.getElementById("disconnect-wallet-btn");

    if (connectBtn) {
      connectBtn.addEventListener("click", () => this.connectWallet());
    }
    if (disconnectBtn) {
      disconnectBtn.addEventListener("click", () => this.disconnectWallet());
    }

    // Reflect wallet state if already connected (e.g. after page re-render)
    if (window.shieldWallet && window.shieldWallet.isConnected()) {
      this.updateWalletUI(window.shieldWallet.getAddress());
    }
  }

  async connectWallet() {
    if (!window.shieldWallet) return;

    const btn = document.getElementById("connect-wallet-btn");
    if (btn) {
      btn.textContent = "Connecting…";
      btn.disabled = true;
    }

    try {
      const account = await window.shieldWallet.connect();
      this.updateWalletUI(account.address);
    } catch (err) {
      this.showMessage(err.message, "error");
      if (btn) {
        btn.textContent = "Connect Shield Wallet";
        btn.disabled = false;
      }
    }
  }

  disconnectWallet() {
    if (!window.shieldWallet) return;
    window.shieldWallet.disconnect();
    this.updateWalletUI(null);
  }

  updateWalletUI(address) {
    const disconnectedEl = document.getElementById("wallet-disconnected");
    const connectedEl = document.getElementById("wallet-connected");
    const addressEl = document.getElementById("wallet-address");
    const connectBtn = document.getElementById("connect-wallet-btn");

    if (address) {
      if (disconnectedEl) disconnectedEl.style.display = "none";
      if (connectedEl) connectedEl.style.display = "block";
      if (addressEl) {
        addressEl.textContent = window.shieldWallet.formatAddress(address);
        addressEl.title = address;
      }
    } else {
      if (disconnectedEl) disconnectedEl.style.display = "block";
      if (connectedEl) connectedEl.style.display = "none";
      if (connectBtn) {
        connectBtn.textContent = "Connect Shield Wallet";
        connectBtn.disabled = false;
      }
    }
  }

  isWagerEnabled() {
    const toggle = document.getElementById("wager-toggle");
    return (
      toggle &&
      toggle.checked &&
      window.shieldWallet &&
      window.shieldWallet.isConnected()
    );
  }

  // ─── Registration / Matchmaking ──────────────────────────────────────────

  register(username) {
    console.log("[Client] Registering:", username);
    this.socket.emit("register", { username });
  }

  async findGame() {
    console.log("[Client] Finding game...");

    // If the player opted to wager, lock the stake before searching
    if (this.isWagerEnabled()) {
      const statusEl = document.getElementById("lobby-status");
      if (statusEl) {
        statusEl.textContent = "Submitting wager transaction…";
        statusEl.classList.add("wallet-pending");
      }

      try {
        const txId = await window.shieldWallet.sendWager();

        if (statusEl) statusEl.textContent = "Waiting for confirmation…";

        await window.shieldWallet.waitForTransaction(txId);

        if (statusEl) {
          statusEl.textContent = "Wager confirmed! Searching for opponent…";
          statusEl.classList.remove("wallet-pending");
        }

        this.socket.emit("find_game", {
          wager_tx: txId,
          aleo_address: window.shieldWallet.getAddress(),
        });
      } catch (err) {
        console.error("[Client] Wager failed:", err);
        this.showMessage(`Wager failed: ${err.message}`, "error");
        if (statusEl) {
          statusEl.textContent = "";
          statusEl.classList.remove("wallet-pending");
        }
        return;
      }
    } else {
      this.socket.emit("find_game", {
        aleo_address: window.shieldWallet
          ? window.shieldWallet.getAddress()
          : null,
      });
    }
  }

  cancelSearch() {
    console.log("[Client] Cancelling search...");
    this.socket.emit("cancel_search", {});
  }

  resign() {
    this.socket.emit("resign", {});
    this.showMessage("You resigned.", "error");
  }

  showScreen(screenName) {
    // Hide all screens
    document.querySelectorAll(".screen").forEach((screen) => {
      screen.classList.remove("active");
    });

    // Show selected screen
    document.getElementById(`${screenName}-screen`).classList.add("active");
  }

  showMessage(message, type = "info") {
    const messageElement = document.getElementById("game-message");
    if (messageElement) {
      messageElement.textContent = message;
      messageElement.style.color =
        type === "error" ? "#dc3545" : type === "success" ? "#28a745" : "#333";

      // Clear after 5 seconds
      setTimeout(() => {
        messageElement.textContent = "";
      }, 5000);
    }
  }

  renderBoard() {
    const boardElement = document.getElementById("chess-board");
    boardElement.innerHTML = "";

    // Apply current theme
    const currentTheme = document.getElementById("theme-select").value;
    BoardThemes.applyTheme(currentTheme, boardElement);

    if (!this.gameState) return;

    const board = this.gameState.board;
    const visibility = this.gameState.visibility;
    const lastMove = this.gameState.last_move;

    // Render board from perspective of player color
    // White sees board from bottom (rank 1), Black sees from top (rank 8)
    const isWhite = this.playerColor === "white";

    for (let rank = 0; rank < 8; rank++) {
      for (let file = 0; file < 8; file++) {
        const displayRank = isWhite ? 7 - rank : rank;
        const displayFile = isWhite ? file : 7 - file;
        const square = displayRank * 8 + displayFile;

        const squareElement = document.createElement("div");
        squareElement.className = "square";
        squareElement.dataset.square = square;

        // Add light/dark class
        const isLight = (displayRank + displayFile) % 2 === 1;
        squareElement.classList.add(isLight ? "light" : "dark");

        // Check visibility (fog of war)
        const isVisible = visibility[square];

        if (isVisible) {
          const piece = board[square];

          if (piece !== 0) {
            const pieceElement = document.createElement("div");
            pieceElement.className = "piece";
            pieceElement.textContent = ChessPieces.getPiece(piece);
            pieceElement.dataset.piece = piece;
            squareElement.appendChild(pieceElement);
          }

          // Highlight last move
          if (
            lastMove &&
            (square === lastMove.from || square === lastMove.to)
          ) {
            squareElement.classList.add("last-move");
          }
        } else {
          // Apply fog of war
          squareElement.classList.add("fog");
        }

        // Add click listener
        squareElement.addEventListener("click", () =>
          this.handleSquareClick(square),
        );

        boardElement.appendChild(squareElement);
      }
    }
  }

  handleSquareClick(square) {
    if (!this.gameState || this.gameState.game_over) return;

    // Check if it's player's turn
    const isMyTurn =
      (this.playerColor === "white" && this.gameState.is_white_turn) ||
      (this.playerColor === "black" && !this.gameState.is_white_turn);

    if (!isMyTurn) {
      this.showMessage("It's not your turn!", "error");
      return;
    }

    const piece = this.gameState.board[square];
    const isVisible = this.gameState.visibility[square];

    if (!isVisible) {
      this.showMessage("Square not visible!", "error");
      return;
    }

    // If no square selected, select this square (if it has player's piece)
    if (this.selectedSquare === null) {
      const pieceColor = ChessPieces.getColor(piece);

      if (pieceColor === this.playerColor) {
        this.selectedSquare = square;
        this.highlightSquare(square);
        console.log("[Client] Selected square:", square);
      }
    } else {
      // Try to move to this square
      this.makeMove(this.selectedSquare, square);
    }
  }

  highlightSquare(square) {
    // Clear previous highlights
    document.querySelectorAll(".square").forEach((sq) => {
      sq.classList.remove("selected");
    });

    // Highlight selected square
    const squareElement = document.querySelector(
      `.square[data-square="${square}"]`,
    );
    if (squareElement) {
      squareElement.classList.add("selected");
    }
  }

  makeMove(fromSquare, toSquare) {
    console.log("[Client] Attempting move:", fromSquare, "->", toSquare);

    // Send move to server
    this.socket.emit("make_move", {
      from: fromSquare,
      to: toSquare,
    });
  }

  updateGameInfo() {
    if (!this.gameState) return;

    // Update player names
    document.getElementById("white-player-name").textContent =
      this.gameState.white_player;
    document.getElementById("black-player-name").textContent =
      this.gameState.black_player;

    // Update ELO
    document.getElementById("white-elo").textContent = this.gameState.white_elo;
    document.getElementById("black-elo").textContent = this.gameState.black_elo;

    // Update turn indicator
    const turnText = this.gameState.is_white_turn
      ? "White's Turn"
      : "Black's Turn";
    document.getElementById("turn-indicator").textContent = turnText;

    // Highlight current player's panel
    const whitePanelElement = document.querySelector(".white-panel");
    const blackPanelElement = document.querySelector(".black-panel");

    if (this.gameState.is_white_turn) {
      whitePanelElement.style.boxShadow = "0 0 15px rgba(102, 126, 234, 0.6)";
      blackPanelElement.style.boxShadow = "none";
    } else {
      blackPanelElement.style.boxShadow = "0 0 15px rgba(102, 126, 234, 0.6)";
      whitePanelElement.style.boxShadow = "none";
    }
  }

  addMoveToHistory(fromSquare, toSquare, player) {
    const moveList = document.getElementById("move-list");
    const moveNumber = this.moveHistory.length + 1;

    const fromAlg = this.squareToAlgebraic(fromSquare);
    const toAlg = this.squareToAlgebraic(toSquare);

    const moveItem = document.createElement("div");
    moveItem.className = "move-item";
    moveItem.textContent = `${moveNumber}. ${fromAlg}-${toAlg}`;

    moveList.appendChild(moveItem);
    this.moveHistory.push({ from: fromSquare, to: toSquare, player });

    // Auto-scroll to bottom
    moveList.scrollTop = moveList.scrollHeight;
  }

  squareToAlgebraic(square) {
    const file = String.fromCharCode(97 + (square % 8)); // a-h
    const rank = Math.floor(square / 8) + 1; // 1-8
    return file + rank;
  }

  showVictoryAnimation(winner, callback) {
    const themeSelect = document.getElementById("victory-theme-select");
    const theme = themeSelect ? themeSelect.value : "anime";

    // Harry Potter: skip animation entirely on draws
    if (winner === 3 && theme !== "anime") {
      callback();
      return;
    }

    const myColorNum = this.playerColor === "white" ? 1 : 2;
    const iLost = winner !== myColorNum && winner !== 3;
    const isDraw = winner === 3;

    let gifPath;
    if (theme === "harry_potter") {
      if (iLost) {
        gifPath = "/static/images/harry_potter/hp3.gif";
      } else {
        const winnerPool = [
          "/static/images/harry_potter/hp1.gif",
          "/static/images/harry_potter/hp2.gif",
          "/static/images/harry_potter/hp4.gif",
        ];
        gifPath = winnerPool[Math.floor(Math.random() * winnerPool.length)];
      }
    } else {
      // Anime theme
      if (isDraw) {
        gifPath = "/static/images/anime/draw.gif";
      } else if (iLost) {
        gifPath = "/static/images/anime/loser.gif";
      } else {
        const winnerPool = [
          "/static/images/anime/victory1.gif",
          "/static/images/anime/victory3.gif",
        ];
        gifPath = winnerPool[Math.floor(Math.random() * winnerPool.length)];
      }
    }

    const overlay = document.createElement("div");
    overlay.className = "victory-overlay";

    const gif = document.createElement("img");
    gif.className = "victory-gif";
    gif.src = gifPath;
    // If the file isn't found, skip straight to the modal
    gif.onerror = () => {
      clearTimeout(timer);
      overlay.remove();
      callback();
    };

    const skip = document.createElement("div");
    skip.className = "victory-skip";
    skip.textContent = "click to skip";

    overlay.appendChild(gif);
    overlay.appendChild(skip);
    document.body.appendChild(overlay);

    // Fade in
    requestAnimationFrame(() =>
      overlay.classList.add("victory-overlay--visible"),
    );

    const dismiss = () => {
      overlay.classList.remove("victory-overlay--visible");
      overlay.addEventListener(
        "transitionend",
        () => {
          overlay.remove();
          callback();
        },
        { once: true },
      );
    };

    // Auto-dismiss after 3.5 s (roughly one loop of the gif)
    const timer = setTimeout(dismiss, 3500);

    // Click-to-skip
    overlay.addEventListener("click", () => {
      clearTimeout(timer);
      dismiss();
    });
  }

  handleGameOver(winner, oldWhiteElo, oldBlackElo, wagerPayout) {
    const winnerNames = { 0: "None", 1: "White", 2: "Black", 3: "Draw" };
    const winnerText =
      winner === 3 ? "Stalemate - Draw!" : `${winnerNames[winner]} wins!`;

    const newWhiteElo = this.gameState.white_elo;
    const newBlackElo = this.gameState.black_elo;
    const whiteChange = oldWhiteElo != null ? newWhiteElo - oldWhiteElo : 0;
    const blackChange = oldBlackElo != null ? newBlackElo - oldBlackElo : 0;
    const displayOldWhite = oldWhiteElo ?? newWhiteElo;
    const displayOldBlack = oldBlackElo ?? newBlackElo;

    // Build wager section
    let wagerHtml = "";
    if (wagerPayout) {
      const { white_wagered, black_wagered, amount } = wagerPayout;
      const aleoAmt = (amount / 1_000_000).toFixed(0);
      if (white_wagered && black_wagered) {
        const total = ((amount * 2) / 1_000_000).toFixed(0);
        if (winner === 3) {
          wagerHtml = `<div class="wager-result"><h3>💰 Wager Result</h3>
            <p>Draw — each player refunded <strong>${aleoAmt} ALEO</strong></p></div>`;
        } else {
          wagerHtml = `<div class="wager-result"><h3>💰 Wager Result</h3>
            <p>${winnerNames[winner]} wins the pot — <strong>${total} ALEO</strong> paid out!</p></div>`;
        }
      } else if (white_wagered || black_wagered) {
        const wagerer = white_wagered ? "White" : "Black";
        wagerHtml = `<div class="wager-result"><h3>💰 Wager Result</h3>
          <p>${wagerer} wagered <strong>${aleoAmt} ALEO</strong> — refunded (opponent did not wager)</p></div>`;
      }
    }

    // Check if this player won but has no wallet connected — they have a pending payout
    const myColorNum = this.playerColor === "white" ? 1 : 2;
    const iWon = winner === myColorNum;
    const iWagered =
      wagerPayout &&
      ((this.playerColor === "white" && wagerPayout.white_wagered) ||
        (this.playerColor === "black" && wagerPayout.black_wagered));
    const bothWagered =
      wagerPayout && wagerPayout.white_wagered && wagerPayout.black_wagered;
    // Need to prompt if: I won, funds exist (both wagered), and I have no wallet
    const needsWalletForPayout =
      iWon && bothWagered && !window.shieldWallet?.isConnected();

    document.getElementById("resign-btn").style.display = "none";
    document.getElementById("new-game-btn").style.display = "inline-block";

    this.showVictoryAnimation(winner, () => {
      const overlay = document.createElement("div");
      overlay.className = "game-over-overlay";

      const box = document.createElement("div");
      box.className = "game-over-box";

      const amount = wagerPayout?.amount ?? 1_000_000;
      const total = ((amount * 2) / 1_000_000).toFixed(0);
      const claimSection = needsWalletForPayout
        ? `<div class="wager-result claim-prompt">
            <h3>🏆 You won ${total} ALEO!</h3>
            <p>Connect your Shield wallet to receive your winnings.</p>
            <button id="claim-wallet-btn" class="btn btn-wallet">Connect Shield Wallet to Claim</button>
           </div>`
        : "";

      box.innerHTML = `
        <h2>🏁 Game Over!</h2>
        <div class="winner-text">${winnerText}</div>
        ${wagerHtml}
        ${claimSection}
        <div class="elo-changes">
          <h3>📊 ELO Rating Changes</h3>
          <p>White (${this.gameState.white_player}):
            ${displayOldWhite} → ${newWhiteElo}
            <span class="elo-change-${whiteChange >= 0 ? "positive" : "negative"}">
              (${whiteChange >= 0 ? "+" : ""}${whiteChange})
            </span>
          </p>
          <p>Black (${this.gameState.black_player}):
            ${displayOldBlack} → ${newBlackElo}
            <span class="elo-change-${blackChange >= 0 ? "positive" : "negative"}">
              (${blackChange >= 0 ? "+" : ""}${blackChange})
            </span>
          </p>
        </div>
        <button class="btn btn-primary" onclick="location.reload()">New Game</button>
      `;

      overlay.appendChild(box);
      document.body.appendChild(overlay);

      // Wire up the claim button if shown
      if (needsWalletForPayout) {
        const claimBtn = document.getElementById("claim-wallet-btn");
        if (claimBtn) {
          claimBtn.addEventListener("click", async () => {
            claimBtn.textContent = "Connecting…";
            claimBtn.disabled = true;
            try {
              const account = await window.shieldWallet.connect();
              this.socket.emit("claim_winnings", {
                aleo_address: account.address,
              });
              this.socket.once("claim_result", (res) => {
                const claimDiv = claimBtn.closest(".claim-prompt");
                if (res.success) {
                  claimDiv.innerHTML = `<h3>✅ Winnings on the way!</h3>
                    <p><strong>${(res.amount / 1_000_000).toFixed(0)} ALEO</strong> transfer submitted to ${window.shieldWallet.formatAddress(account.address)}</p>`;
                } else {
                  claimDiv.innerHTML = `<p class="error-text">Claim failed: ${res.error}</p>`;
                }
              });
            } catch (err) {
              claimBtn.textContent = "Connect Shield Wallet to Claim";
              claimBtn.disabled = false;
              console.error("[Claim] Wallet connect failed:", err);
            }
          });
        }
      }
    });
  }
}

// Initialize game when page loads
document.addEventListener("DOMContentLoaded", () => {
  console.log("[Client] Initializing Knightfall Chess...");
  window.game = new KnightfallGame();
});
