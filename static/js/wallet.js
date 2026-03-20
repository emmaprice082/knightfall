/**
 * Knightfall Chess - Shield Wallet Integration
 *
 * Wager flow:
 *   1. Player connects Shield wallet
 *   2. Player opts in to wager → sendWager() transfers ALEO to the custodial
 *      wallet via credits.aleo/transfer_public
 *   3. Server receives the tx ID, verifies it on-chain, then starts the game
 *      once both players have confirmed wager txs
 *   4. At game end the server (controlling the custodial key) pays the winner
 */

// Custodial wallet that holds wagers during gameplay and pays the winner
const CUSTODIAL_ADDRESS =
  "aleo17js8w4w7hwaa6ez9t2za4cccqs0xcer2xjg5cxjw9vkszqkq6cpsj3ppzr";

const DEFAULT_NETWORK = "testnet";
const DEFAULT_STAKE_MICROCREDITS = 1_000_000; // 1 ALEO
const DEFAULT_FEE_MICROCREDITS  = 100_000;   // 0.1 ALEO

class ShieldWallet {
  constructor() {
    this.account = null;   // { address, viewKey?, privateKey? }
    this.network = DEFAULT_NETWORK;
    this._listeners = {};
  }

  // ─── Detection ────────────────────────────────────────────────────────────

  isAvailable() {
    return typeof window !== "undefined" && !!window.shield;
  }

  // ─── Connect ──────────────────────────────────────────────────────────────

  async connect(network = DEFAULT_NETWORK) {
    if (!this.isAvailable()) {
      throw new Error(
        "Shield wallet extension not found. " +
        "Please install the Shield wallet and refresh the page."
      );
    }

    this.network = network;

    // Request permission for credits.aleo (needed for transfer_public wagers).
    // Passing an empty array would allow all programs — either works.
    const account = await window.shield.connect(
      network,
      "NO_DECRYPT",
      ["credits.aleo"]
    );

    if (!account) {
      throw new Error("Connection cancelled by user.");
    }

    this.account = account;
    this._emit("connect", { address: account.address, network });
    console.log("[ShieldWallet] Connected:", account.address);
    return account;
  }

  // ─── Disconnect ───────────────────────────────────────────────────────────

  disconnect() {
    // Fire-and-forget — don't await shield.disconnect() because it may hang
    // waiting for user action in the extension popup, blocking our UI update.
    if (this.isAvailable()) {
      window.shield.disconnect().catch((err) =>
        console.warn("[ShieldWallet] shield.disconnect error (ignored):", err)
      );
    }

    this.account = null;
    this._emit("disconnect", {});
    console.log("[ShieldWallet] Disconnected (local state cleared)");
  }

  // ─── Wager ────────────────────────────────────────────────────────────────

  /**
   * Transfer ALEO to the custodial wallet to lock in the player's wager.
   * Uses credits.aleo/transfer_public — a real credit transfer the chain can verify.
   *
   * @param {number} amountMicrocredits  default 1 ALEO (1_000_000 microcredits)
   * @returns {Promise<string>} transactionId
   */
  async sendWager(amountMicrocredits = DEFAULT_STAKE_MICROCREDITS) {
    if (!this.isAvailable()) throw new Error("Shield wallet not available.");
    if (!this.account) throw new Error("Wallet not connected. Call connect() first.");

    console.log(
      `[ShieldWallet] sendWager: ${amountMicrocredits} microcredits → ${CUSTODIAL_ADDRESS}`
    );

    const result = await window.shield.executeTransaction({
      program: "credits.aleo",
      function: "transfer_public",
      inputs: [
        CUSTODIAL_ADDRESS,
        `${amountMicrocredits}u64`,
      ],
      fee: DEFAULT_FEE_MICROCREDITS,
      network: this.network,
      privateFee: false,
    });

    console.log("[ShieldWallet] wager submitted:", result.transactionId);
    return result.transactionId;
  }

  // ─── Transaction status ───────────────────────────────────────────────────

  /**
   * Poll until the transaction is Accepted/Finalized, or throw on failure/timeout.
   */
  async waitForTransaction(
    transactionId,
    pollIntervalMs = 3000,
    timeoutMs = 120_000
  ) {
    if (!this.isAvailable()) throw new Error("Shield wallet not available.");

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

  // ─── Helpers ──────────────────────────────────────────────────────────────

  getAddress() { return this.account?.address ?? null; }
  isConnected() { return !!this.account; }

  /** Truncate for display: aleo1abcd...wxyz */
  formatAddress(address) {
    if (!address || address.length < 12) return address;
    return `${address.slice(0, 9)}...${address.slice(-4)}`;
  }

  // ─── Internal event bus ───────────────────────────────────────────────────

  on(event, cb) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(cb);
  }

  off(event, cb) {
    if (!this._listeners[event]) return;
    this._listeners[event] = this._listeners[event].filter((f) => f !== cb);
  }

  _emit(event, data) {
    (this._listeners[event] || []).forEach((cb) => {
      try { cb(data); } catch (e) { console.error("[ShieldWallet] listener error:", e); }
    });
  }
}

window.shieldWallet = new ShieldWallet();
