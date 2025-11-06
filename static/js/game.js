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

    // Load saved theme
    const savedTheme = BoardThemes.loadSavedTheme();
    document.getElementById("theme-select").value = savedTheme;
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
        this.handleGameOver(data.winner);
      }
    });

    this.socket.on("move_rejected", (data) => {
      console.log("[Client] Move rejected:", data.error);
      this.showMessage(`Invalid move: ${data.error}`, "error");
      this.selectedSquare = null;
      this.renderBoard();
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

  register(username) {
    console.log("[Client] Registering:", username);
    this.socket.emit("register", { username });
  }

  findGame() {
    console.log("[Client] Finding game...");
    this.socket.emit("find_game", {});
  }

  cancelSearch() {
    console.log("[Client] Cancelling search...");
    this.socket.emit("cancel_search", {});
  }

  resign() {
    // TODO: Implement resign functionality
    this.showMessage("Resigned!", "error");
    setTimeout(() => {
      this.showScreen("lobby");
    }, 2000);
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
          this.handleSquareClick(square)
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
      `.square[data-square="${square}"]`
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

  handleGameOver(winner) {
    const winnerNames = {
      0: "None",
      1: "White",
      2: "Black",
      3: "Draw",
    };

    const winnerText =
      winner === 3 ? "Stalemate - Draw!" : `${winnerNames[winner]} wins!`;

    // Create game over overlay
    const overlay = document.createElement("div");
    overlay.className = "game-over-overlay";

    const box = document.createElement("div");
    box.className = "game-over-box";

    const oldWhiteElo = this.gameState.white_elo;
    const oldBlackElo = this.gameState.black_elo;

    box.innerHTML = `
            <h2>🏁 Game Over!</h2>
            <div class="winner-text">${winnerText}</div>
            <div class="elo-changes">
                <h3>📊 ELO Rating Changes</h3>
                <p>White (${this.gameState.white_player}): ${oldWhiteElo} → ${
      this.gameState.white_elo
    } 
                   <span class="elo-change-${
                     this.gameState.white_elo > oldWhiteElo
                       ? "positive"
                       : "negative"
                   }">
                       (${
                         this.gameState.white_elo - oldWhiteElo >= 0 ? "+" : ""
                       }${this.gameState.white_elo - oldWhiteElo})
                   </span>
                </p>
                <p>Black (${this.gameState.black_player}): ${oldBlackElo} → ${
      this.gameState.black_elo
    }
                   <span class="elo-change-${
                     this.gameState.black_elo > oldBlackElo
                       ? "positive"
                       : "negative"
                   }">
                       (${
                         this.gameState.black_elo - oldBlackElo >= 0 ? "+" : ""
                       }${this.gameState.black_elo - oldBlackElo})
                   </span>
                </p>
            </div>
            <button class="btn btn-primary" onclick="location.reload()">New Game</button>
        `;

    overlay.appendChild(box);
    document.body.appendChild(overlay);

    // Show new game button
    document.getElementById("resign-btn").style.display = "none";
    document.getElementById("new-game-btn").style.display = "inline-block";
  }
}

// Initialize game when page loads
document.addEventListener("DOMContentLoaded", () => {
  console.log("[Client] Initializing Knightfall Chess...");
  window.game = new KnightfallGame();
});
