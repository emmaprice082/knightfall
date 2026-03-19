/**
 * Knightfall Chess - Shield Wallet Integration
 *
 * Wraps window.shield (Galileo/Shield browser extension) to:
 *   - Connect a player's Aleo wallet
 *   - Execute the collect_stake transition to wager on a game
 *   - Poll transaction status until confirmed or failed
 */

const KNIGHTFALL_PROGRAM = "provable_toronoto25_knightfall.aleo";
const DEFAULT_NETWORK = "testnet";
const DEFAULT_STAKE_MICROCREDITS = 1_000_000; // 1 ALEO
const DEFAULT_FEE_MICROCREDITS = 100_000;     // 0.1 ALEO

class ShieldWallet {
  constructor() {
    this.account = null;       // { address, viewKey?, privateKey? }
    this.network = DEFAULT_NETWORK;
    this._listeners = {};      // eventName -> [callback]
  }

  // ─── Detection ────────────────────────────────────────────────────────────

  isAvailable() {
    return typeof window !== "undefined" && !!window.shield;
  }

  // ─── Connect ──────────────────────────────────────────────────────────────

  /**
   * Prompt the Shield wallet to connect.
   * Returns the connected account { address } or null on failure.
   */
  async connect(network = DEFAULT_NETWORK) {
    if (!this.isAvailable()) {
      throw new Error(
        "Shield wallet extension not found. " +
        "Please install the Shield wallet and refresh the page."
      );
    }

    this.network = network;

    try {
      const account = await window.shield.connect(
        network,
        "NO_DECRYPT",
        [KNIGHTFALL_PROGRAM]
      );

      if (!account) {
        throw new Error("Connection cancelled by user.");
      }

      this.account = account;
      this._emit("connect", { address: account.address, network });
      console.log("[ShieldWallet] Connected:", account.address);
      return account;
    } catch (err) {
      console.error("[ShieldWallet] Connect failed:", err);
      throw err;
    }
  }

  // ─── Disconnect ───────────────────────────────────────────────────────────

  async disconnect() {
    if (!this.isAvailable()) return;
    try {
      await window.shield.disconnect();
    } catch (_) { /* ignore */ }
    const address = this.account?.address;
    this.account = null;
    this._emit("disconnect", { address });
    console.log("[ShieldWallet] Disconnected");
  }

  // ─── Stake ────────────────────────────────────────────────────────────────

  /**
   * Execute collect_stake on-chain so the player's wager is locked.
   *
   * @param {string} opponentAddress  - Aleo address of the opponent
   * @param {number} amountMicrocredits - Wager in microcredits (default 1 ALEO)
   * @returns {Promise<string>} transactionId
   */
  async collectStake(
    opponentAddress,
    amountMicrocredits = DEFAULT_STAKE_MICROCREDITS
  ) {
    if (!this.isAvailable()) {
      throw new Error("Shield wallet not available.");
    }
    if (!this.account) {
      throw new Error("Wallet not connected. Call connect() first.");
    }

    const ownerAddress = this.account.address;

    console.log(
      `[ShieldWallet] collectStake: owner=${ownerAddress} ` +
      `opponent=${opponentAddress} amount=${amountMicrocredits}`
    );

    const result = await window.shield.executeTransaction({
      program: KNIGHTFALL_PROGRAM,
      function: "collect_stake",
      inputs: [
        ownerAddress,
        opponentAddress,
        `${amountMicrocredits}u64`,
      ],
      fee: DEFAULT_FEE_MICROCREDITS,
      network: this.network,
      privateFee: false,
    });

    console.log("[ShieldWallet] collectStake submitted:", result.transactionId);
    return result.transactionId;
  }

  // ─── Transaction status ───────────────────────────────────────────────────

  /**
   * Poll for transaction status.
   * Resolves with { status, transactionId } once the tx is Accepted/Rejected,
   * or rejects after timeoutMs.
   *
   * @param {string} transactionId
   * @param {number} pollIntervalMs
   * @param {number} timeoutMs
   */
  async waitForTransaction(
    transactionId,
    pollIntervalMs = 3000,
    timeoutMs = 120_000
  ) {
    if (!this.isAvailable()) {
      throw new Error("Shield wallet not available.");
    }

    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
      const status = await window.shield.transactionStatus(transactionId);
      console.log("[ShieldWallet] tx status:", status);

      if (status.status === "Accepted" || status.status === "Finalized") {
        return status;
      }
      if (status.status === "Rejected" || status.error) {
        throw new Error(
          `Transaction ${transactionId} failed: ${status.error || status.status}`
        );
      }

      await new Promise((res) => setTimeout(res, pollIntervalMs));
    }

    throw new Error(
      `Transaction ${transactionId} timed out after ${timeoutMs / 1000}s`
    );
  }

  // ─── Address helpers ──────────────────────────────────────────────────────

  getAddress() {
    return this.account?.address ?? null;
  }

  isConnected() {
    return !!this.account;
  }

  /** Truncate address for display: aleo1abcd...wxyz */
  formatAddress(address) {
    if (!address || address.length < 12) return address;
    return `${address.slice(0, 9)}...${address.slice(-4)}`;
  }

  // ─── Internal event bus ───────────────────────────────────────────────────

  on(event, callback) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(callback);
  }

  off(event, callback) {
    if (!this._listeners[event]) return;
    this._listeners[event] = this._listeners[event].filter(
      (cb) => cb !== callback
    );
  }

  _emit(event, data) {
    (this._listeners[event] || []).forEach((cb) => {
      try { cb(data); } catch (err) { console.error("[ShieldWallet] listener error:", err); }
    });
  }
}

// Singleton
window.shieldWallet = new ShieldWallet();
