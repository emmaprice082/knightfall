#!/usr/bin/env python3
"""
Leo CLI Interface - Direct interface to Leo smart contracts.
All game logic validation goes through Leo; leaderboard updates go on-chain.
"""

import subprocess
import re
import json
import os
import threading
import urllib.request
from typing import Dict, List, Tuple, Optional
from game_state import GameState


ALEO_API = "https://api.explorer.provable.com/v1/testnet"
LEADERBOARD_PROGRAM = "knightfall_leaderboard.aleo"


class LeoCliInterface:
    """
    Interface to Leo smart contracts via CLI.
    - Move validation / visibility / ELO: `leo run` against knightfall_logic
    - Leaderboard persistence: `snarkos developer execute` against deployed contract
    """

    def __init__(self, logic_path: str = None):
        self.logic_path = logic_path or os.path.join(
            os.path.dirname(__file__),
            '../knightfall-aleo/knightfall_logic'
        )

        try:
            result = subprocess.run(
                ['leo', '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"[Leo CLI] Leo version: {result.stdout.strip()}")
            else:
                print("[Leo CLI] Warning: `leo --version` returned non-zero")
        except Exception as e:
            print(f"[Leo CLI] Warning: could not verify Leo installation: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _run_leo_function(self, function_name: str, *args) -> Optional[Dict]:
        """Run `leo run <function> <args>` and return parsed stdout."""
        try:
            cmd = ['leo', 'run', function_name] + [str(a) for a in args]
            print(f"[Leo CLI] Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=self.logic_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"[Leo CLI] Error running {function_name}: {result.stderr[:300]}")
                return None

            output = result.stdout
            print(f"[Leo CLI] Output: {output[:200]}")
            return {'success': True, 'output': output}

        except subprocess.TimeoutExpired:
            print(f"[Leo CLI] Timeout running {function_name}")
            return None
        except Exception as e:
            print(f"[Leo CLI] Exception running {function_name}: {e}")
            return None

    @staticmethod
    def _parse_bool(output: str) -> Optional[bool]:
        """Parse a Leo bool output: `• true` or `• false`."""
        m = re.search(r'•\s*(true|false)', output)
        if m:
            return m.group(1) == 'true'
        return None

    @staticmethod
    def _parse_u32_tuple(output: str) -> Optional[Tuple[int, int]]:
        """
        Parse two successive Leo u32 outputs.
        `leo run` emits each return value on its own bullet line:
            • 1184u32
            • 1216u32
        """
        values = re.findall(r'•\s*(\d+)u32', output)
        if len(values) >= 2:
            return int(values[0]), int(values[1])
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Move validation
    # ──────────────────────────────────────────────────────────────────────────

    def validate_move_leo(self, game: GameState, from_square: int, to_square: int) -> bool:
        """
        Validate a move using Python logic that mirrors Leo's is_move_legal.
        Full Leo CLI integration is the long-term goal; Python fallback is exact.
        """
        from leo_interface_updated import LeoInterface
        return LeoInterface().validate_move(game, from_square, to_square)

    # ──────────────────────────────────────────────────────────────────────────
    # Fog-of-war visibility
    # ──────────────────────────────────────────────────────────────────────────

    def calculate_visibility_leo(self, game: GameState, for_white: bool) -> List[bool]:
        """Return list of 64 booleans indicating visible squares for one side."""
        from leo_interface_updated import LeoInterface
        bitboard = LeoInterface().calculate_visibility(game, for_white)
        result = [bool((bitboard >> sq) & 1) for sq in range(64)]
        print(f"[Leo CLI] Visibility ({'white' if for_white else 'black'}): "
              f"{sum(result)}/64 visible")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # ELO calculation  (Leo CLI → Python fallback)
    # ──────────────────────────────────────────────────────────────────────────

    def calculate_elo_leo(self, white_elo: int, black_elo: int, winner: int) -> Tuple[int, int]:
        """
        Calculate updated ELO ratings.
        Tries `leo run calculate_elo_updates` first; falls back to Python mirror.
        winner: 1=white wins, 2=black wins, 3=draw
        """
        result = self._run_leo_function(
            'calculate_elo_updates',
            f"{white_elo}u32",
            f"{black_elo}u32",
            f"{winner}u8",
        )

        if result:
            parsed = self._parse_u32_tuple(result['output'])
            if parsed:
                new_white, new_black = parsed
                print(f"[Leo CLI] ELO (via Leo): white {white_elo}→{new_white}, "
                      f"black {black_elo}→{new_black}")
                return new_white, new_black
            print("[Leo CLI] Could not parse ELO output — falling back to Python")

        from leo_interface_updated import LeoInterface
        return LeoInterface().calculate_elo_update(white_elo, black_elo, winner)

    # ──────────────────────────────────────────────────────────────────────────
    # On-chain leaderboard  (knightfall_leaderboard.aleo)
    # ──────────────────────────────────────────────────────────────────────────

    def fetch_player_elo(self, address: str) -> Optional[int]:
        """
        Query the on-chain leaderboard for a player's current ELO.
        Returns None on any failure (caller should default to 1200).
        """
        try:
            url = (f"{ALEO_API}/program/{LEADERBOARD_PROGRAM}"
                   f"/mapping/player_elo/{address}")
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Knightfall/1.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = resp.read().decode().strip()
                # API returns a JSON string like "1200u32" or null
                data = json.loads(raw)
                if data is None:
                    return None
                elo_str = str(data).strip('"')
                elo = int(re.sub(r'[^\d]', '', elo_str))
                if 100 <= elo <= 3000:
                    print(f"[Leaderboard] ELO for {address[:12]}…: {elo}")
                    return elo
        except Exception as e:
            print(f"[Leaderboard] Could not fetch ELO for {address[:12]}…: {e}")
        return None

    def record_game_leaderboard(
        self,
        white_address: str,
        black_address: str,
        winner: int,
    ):
        """
        Record a completed game result on-chain via knightfall_leaderboard.aleo.
        Runs in a background thread — does not block the game flow.
        Requires CUSTODIAL_PRIVATE_KEY env var (same key used for payouts).
        winner: 1=white, 2=black, 3=draw
        """
        private_key = os.environ.get('CUSTODIAL_PRIVATE_KEY')
        if not private_key:
            print("[Leaderboard] CUSTODIAL_PRIVATE_KEY not set — skipping on-chain record")
            return

        def _record():
            cmd = [
                'snarkos', 'developer', 'execute',
                LEADERBOARD_PROGRAM, 'record_game',
                white_address,
                black_address,
                f'{winner}u8',
                '--private-key', private_key,
                '--query', 'https://api.explorer.provable.com/v1',
                '--broadcast', f'{ALEO_API}/transaction/broadcast',
                '--network', '1',
                '--priority-fee', '100000',
            ]
            w_short = white_address[:12]
            b_short = black_address[:12]
            print(f"[Leaderboard] Recording game: {w_short}… vs {b_short}…, winner={winner}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    print(f"[Leaderboard] ✅ Recorded: {result.stdout.strip()[:200]}")
                else:
                    out = result.stdout.strip()[:300]
                    err = result.stderr.strip()[:300]
                    print(f"[Leaderboard] ❌ Failed (rc={result.returncode})")
                    if out: print(f"[Leaderboard]   stdout: {out}")
                    if err: print(f"[Leaderboard]   stderr: {err}")
            except subprocess.TimeoutExpired:
                print(f"[Leaderboard] ❌ Timed out recording game")
            except Exception as e:
                print(f"[Leaderboard] ❌ Exception: {e}")

        threading.Thread(target=_record, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # Misc
    # ──────────────────────────────────────────────────────────────────────────

    def check_game_over_leo(self, game: GameState) -> Tuple[bool, int]:
        """Checkmate detection is too expensive for Leo — always done in Python."""
        from leo_interface_updated import LeoInterface
        return LeoInterface().check_game_over(game)

    def _board_array_to_leo(self, board_array: List[int]) -> str:
        return "[" + ", ".join(f"{p}u8" for p in board_array) + "]"

    def compile_leo_program(self) -> bool:
        try:
            result = subprocess.run(
                ['leo', 'build'],
                cwd=self.logic_path,
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print("[Leo CLI] ✅ Compiled")
                return True
            print(f"[Leo CLI] ❌ Compile failed: {result.stderr[:200]}")
            return False
        except Exception as e:
            print(f"[Leo CLI] Compile exception: {e}")
            return False


if __name__ == "__main__":
    cli = LeoCliInterface()

    print("\n── ELO calculation ──")
    w, b = cli.calculate_elo_leo(1200, 1200, 1)
    print(f"   white: 1200 → {w},  black: 1200 → {b}")

    print("\n── On-chain ELO fetch (will fail if address not registered) ──")
    elo = cli.fetch_player_elo(
        "aleo17js8w4w7hwaa6ez9t2za4cccqs0xcer2xjg5cxjw9vkszqkq6cpsj3ppzr"
    )
    print(f"   ELO: {elo}")
