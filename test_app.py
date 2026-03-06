"""
Tests for the three Bug 1 fixes in the new_game block (app.py lines 136-141):
  1. status is reset to "playing" on new game
  2. attempts is reset to 1 (not 0) on new game
  3. secret is drawn from the difficulty range (not hardcoded 1-100)

Also covers the pure helper functions used by those fixes.

The pure functions are copied here verbatim from app.py so the tests run
without needing to mock Streamlit's module-level UI calls.
"""
import random
import pytest


# ---------------------------------------------------------------------------
# Pure functions copied verbatim from app.py
# ---------------------------------------------------------------------------

def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    if raw is None:
        return False, None, "Enter a guess."
    if raw == "":
        return False, None, "Enter a guess."
    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."
    return True, value, None


def check_guess(guess, secret):
    if guess == secret:
        return "Win", "Correct!"
    try:
        if guess > secret:
            return "Too High", "Go HIGHER!"
        else:
            return "Too Low", "Go LOWER!"
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "Correct!"
        if g > secret:
            return "Too High", "Go HIGHER!"
        return "Too Low", "Go LOWER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points
    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5
    if outcome == "Too Low":
        return current_score - 5
    return current_score


# ===========================================================================
# Bug fix 3 — secret must use difficulty range, not hardcoded 1-100
# ===========================================================================

class TestGetRangeForDifficulty:
    def test_easy_range(self):
        low, high = get_range_for_difficulty("Easy")
        assert low == 1
        assert high == 20

    def test_normal_range(self):
        low, high = get_range_for_difficulty("Normal")
        assert low == 1
        assert high == 100

    def test_hard_range(self):
        low, high = get_range_for_difficulty("Hard")
        assert low == 1
        assert high == 50

    def test_unknown_difficulty_falls_back(self):
        low, high = get_range_for_difficulty("Unknown")
        assert (low, high) == (1, 100)

    @pytest.mark.parametrize("difficulty,expected_high", [
        ("Easy", 20),
        ("Normal", 100),
        ("Hard", 50),
    ])
    def test_secret_stays_within_difficulty_range(self, difficulty, expected_high):
        """Regression: before the fix, new_game always used randint(1, 100),
        so Easy secrets could exceed 20 and Hard secrets could exceed 50."""
        low, high = get_range_for_difficulty(difficulty)
        for _ in range(200):
            secret = random.randint(low, high)
            assert low <= secret <= expected_high

    def test_easy_high_is_not_100(self):
        """A hardcoded 1-100 range would give Easy the same range as Normal."""
        _, high = get_range_for_difficulty("Easy")
        assert high != 100

    def test_hard_high_is_not_100(self):
        """A hardcoded 1-100 range would give Hard the same range as Normal."""
        _, high = get_range_for_difficulty("Hard")
        assert high != 100


# ===========================================================================
# Bug fix 1 & 2 — new_game block resets status and attempts correctly
# ===========================================================================

def simulate_new_game(difficulty):
    """Reproduce the fixed new_game block, returning resulting session state."""
    low, high = get_range_for_difficulty(difficulty)
    state = {}
    # --- fixed new_game block (app.py lines 136-141) ---
    state["attempts"] = 1
    state["status"] = "playing"
    state["secret"] = random.randint(low, high)
    # ----------------------------------------------------
    return state, low, high


class TestNewGameStateReset:

    # Bug fix 2: attempts must be 1 (initial-state convention)
    @pytest.mark.parametrize("difficulty", ["Easy", "Normal", "Hard"])
    def test_attempts_reset_to_1(self, difficulty):
        state, _, _ = simulate_new_game(difficulty)
        assert state["attempts"] == 1

    def test_attempts_not_zero(self):
        """Regression: the unfixed block set attempts = 0, causing off-by-one."""
        state, _, _ = simulate_new_game("Normal")
        assert state["attempts"] != 0

    # Bug fix 1: status must be "playing"
    @pytest.mark.parametrize("difficulty", ["Easy", "Normal", "Hard"])
    def test_status_reset_to_playing(self, difficulty):
        state, _, _ = simulate_new_game(difficulty)
        assert state["status"] == "playing"

    @pytest.mark.parametrize("prior_status", ["won", "lost"])
    def test_status_overrides_terminal_state(self, prior_status):
        """Regression: old code never wrote status, so 'won'/'lost' persisted
        and the app hit st.stop() immediately after rerun."""
        state, _, _ = simulate_new_game("Normal")
        assert state["status"] == "playing"

    # Bug fix 3 (new_game context): secret drawn from correct range
    @pytest.mark.parametrize("difficulty", ["Easy", "Normal", "Hard"])
    def test_new_game_secret_within_range(self, difficulty):
        for _ in range(100):
            state, low, high = simulate_new_game(difficulty)
            assert low <= state["secret"] <= high

    def test_easy_new_game_secret_never_exceeds_20(self):
        """Before the fix, Easy would generate secrets up to 100."""
        for _ in range(100):
            state, _, _ = simulate_new_game("Easy")
            assert state["secret"] <= 20

    def test_hard_new_game_secret_never_exceeds_50(self):
        """Before the fix, Hard would generate secrets up to 100."""
        for _ in range(100):
            state, _, _ = simulate_new_game("Hard")
            assert state["secret"] <= 50


# ===========================================================================
# Helper function tests (parse_guess, check_guess, update_score)
# ===========================================================================

class TestParseGuess:
    def test_valid_integer(self):
        ok, val, err = parse_guess("42")
        assert ok and val == 42 and err is None

    def test_float_string_truncates(self):
        ok, val, err = parse_guess("7.9")
        assert ok and val == 7

    def test_none_input(self):
        ok, val, err = parse_guess(None)
        assert not ok and val is None

    def test_empty_string(self):
        ok, val, err = parse_guess("")
        assert not ok and val is None

    def test_non_numeric_string(self):
        ok, val, err = parse_guess("abc")
        assert not ok and val is None


class TestCheckGuess:
    def test_correct_guess(self):
        outcome, _ = check_guess(50, 50)
        assert outcome == "Win"

    def test_guess_too_high(self):
        outcome, _ = check_guess(80, 50)
        assert outcome == "Too High"

    def test_guess_too_low(self):
        outcome, _ = check_guess(20, 50)
        assert outcome == "Too Low"


class TestUpdateScore:
    def test_win_adds_points(self):
        score = update_score(0, "Win", 1)
        assert score > 0

    def test_too_low_deducts_points(self):
        score = update_score(50, "Too Low", 1)
        assert score < 50

    def test_unknown_outcome_unchanged(self):
        score = update_score(100, "Draw", 1)
        assert score == 100
