/**
 * Board Themes - Customizable color schemes
 * Handles theme switching and persistence
 */

const BoardThemes = {
  themes: {
    classic: {
      name: "Classic",
      light: "#f0d9b5",
      dark: "#b58863",
    },
    modern: {
      name: "Modern Blue",
      light: "#e8eef2",
      dark: "#7fa3c7",
    },
    wooden: {
      name: "Wooden",
      light: "#f0d0a0",
      dark: "#8b4513",
    },
    marble: {
      name: "Marble",
      light: "#f8f8ff",
      dark: "#a9a9a9",
    },
    neon: {
      name: "Neon",
      light: "#00ffff",
      dark: "#ff00ff",
    },
    ocean: {
      name: "Ocean",
      light: "#b8e6f3",
      dark: "#2c5f7d",
    },
    forest: {
      name: "Forest",
      light: "#c8e6c9",
      dark: "#2e7d32",
    },
    sunset: {
      name: "Sunset",
      light: "#ffe4b5",
      dark: "#ff6347",
    },
  },

  currentTheme: "classic",

  /**
   * Apply theme to board
   */
  applyTheme: function (themeName, boardElement) {
    // Remove all theme classes
    for (let theme in this.themes) {
      boardElement.classList.remove(`theme-${theme}`);
    }

    // Add new theme class
    if (this.themes[themeName]) {
      boardElement.classList.add(`theme-${themeName}`);
      this.currentTheme = themeName;

      // Save to localStorage
      localStorage.setItem("knightfall-theme", themeName);
    }
  },

  /**
   * Load saved theme from localStorage
   */
  loadSavedTheme: function () {
    const saved = localStorage.getItem("knightfall-theme");
    return saved && this.themes[saved] ? saved : "classic";
  },

  /**
   * Get all theme names
   */
  getThemeNames: function () {
    return Object.keys(this.themes);
  },
};

// Export for use in other modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = BoardThemes;
}
