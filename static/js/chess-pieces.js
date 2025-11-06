/**
 * Chess Pieces - 2D Unicode Representation
 * Handles piece rendering and identification
 */

const ChessPieces = {
  // White pieces (1-6)
  1: "♙", // White Pawn
  2: "♘", // White Knight
  3: "♗", // White Bishop
  4: "♖", // White Rook
  5: "♕", // White Queen
  6: "♔", // White King

  // Black pieces (7-12)
  7: "♟", // Black Pawn
  8: "♞", // Black Knight
  9: "♝", // Black Bishop
  10: "♜", // Black Rook
  11: "♛", // Black Queen
  12: "♚", // Black King

  // Empty square
  0: "",

  /**
   * Get piece unicode character
   */
  getPiece: function (pieceCode) {
    return this[pieceCode] || "";
  },

  /**
   * Check if piece is white
   */
  isWhite: function (pieceCode) {
    return pieceCode >= 1 && pieceCode <= 6;
  },

  /**
   * Check if piece is black
   */
  isBlack: function (pieceCode) {
    return pieceCode >= 7 && pieceCode <= 12;
  },

  /**
   * Get piece name
   */
  getName: function (pieceCode) {
    const names = {
      1: "White Pawn",
      2: "White Knight",
      3: "White Bishop",
      4: "White Rook",
      5: "White Queen",
      6: "White King",
      7: "Black Pawn",
      8: "Black Knight",
      9: "Black Bishop",
      10: "Black Rook",
      11: "Black Queen",
      12: "Black King",
      0: "Empty",
    };
    return names[pieceCode] || "Unknown";
  },

  /**
   * Get piece type (1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king)
   */
  getType: function (pieceCode) {
    if (pieceCode === 0) return 0;
    return pieceCode <= 6 ? pieceCode : pieceCode - 6;
  },

  /**
   * Get piece color
   */
  getColor: function (pieceCode) {
    if (pieceCode === 0) return null;
    return pieceCode <= 6 ? "white" : "black";
  },
};

// Export for use in other modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = ChessPieces;
}
