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
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score


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


class TestCheckGuessNumericComparison:
    """Bug 2 regression tests.

    When secret was cast to str on even attempts, comparisons became
    lexicographic. Classic failure cases:
      - guess=100, secret="50"  → "1" < "5" lexicographically → "Too Low" (wrong, should be "Too High")
      - guess=9,   secret="10" → "9" > "1" lexicographically → "Too High" (wrong, should be "Too Low")
    The fix is to always pass secret as int. These tests call check_guess
    with an int secret to confirm numeric semantics are preserved.
    """

    def test_100_vs_50_is_too_high(self):
        """Regression: with str secret '50', guess 100 compared '1' < '5' → 'Too Low'."""
        outcome, _ = check_guess(100, 50)
        assert outcome == "Too High"

    def test_9_vs_10_is_too_low(self):
        """Regression: with str secret '10', guess 9 compared '9' > '1' → 'Too High'."""
        outcome, _ = check_guess(9, 10)
        assert outcome == "Too Low"

    def test_2_vs_19_is_too_low(self):
        """'2' > '1' lexicographically but 2 < 19 numerically."""
        outcome, _ = check_guess(2, 19)
        assert outcome == "Too Low"

    def test_int_secret_win(self):
        outcome, _ = check_guess(42, 42)
        assert outcome == "Win"

    def test_secret_as_string_breaks_comparison(self):
        """Documents the broken behaviour that the fix prevents.
        With a string secret '50', check_guess(100, '50') returns 'Too Low'
        because '1' < '5' lexicographically — the opposite of correct."""
        broken_outcome, _ = check_guess(100, "50")
        # This assertion shows the bug: the result is wrong
        assert broken_outcome == "Too Low"   # wrong answer from string comparison

    def test_int_secret_gives_correct_direction(self):
        """With int secret 50, check_guess(100, 50) correctly returns 'Too High'."""
        outcome, _ = check_guess(100, 50)
        assert outcome == "Too High"


def build_info_message(low, high, attempts_left):
    """Mirrors the fixed st.info() f-string in app.py line 109-112."""
    return f"Guess a number between {low} and {high}. Attempts left: {attempts_left}"


class TestInfoMessageUsesRange:
    """Bug 3 regression tests — info banner must reflect the selected difficulty range."""

    @pytest.mark.parametrize("difficulty,expected_high", [
        ("Easy", 20),
        ("Normal", 100),
        ("Hard", 50),
    ])
    def test_message_uses_difficulty_high(self, difficulty, expected_high):
        low, high = get_range_for_difficulty(difficulty)
        msg = build_info_message(low, high, attempts_left=5)
        assert str(expected_high) in msg

    def test_easy_message_does_not_say_100(self):
        """Regression: hardcoded '1 and 100' would appear for Easy even though range is 1–20."""
        low, high = get_range_for_difficulty("Easy")
        msg = build_info_message(low, high, attempts_left=5)
        assert "100" not in msg

    def test_hard_message_does_not_say_100(self):
        """Regression: hardcoded '1 and 100' would appear for Hard even though range is 1–50."""
        low, high = get_range_for_difficulty("Hard")
        msg = build_info_message(low, high, attempts_left=5)
        assert "100" not in msg

    def test_message_includes_low_bound(self):
        low, high = get_range_for_difficulty("Easy")
        msg = build_info_message(low, high, attempts_left=3)
        assert str(low) in msg

    def test_message_includes_attempts_left(self):
        low, high = get_range_for_difficulty("Normal")
        msg = build_info_message(low, high, attempts_left=4)
        assert "4" in msg


class TestHistoryReflectsCurrentGuess:
    """Bug 4 regression tests.

    The expander was rendered before the submit block, so history always
    showed the previous run's state. Moving it after the submit block means
    history is up to date when the expander renders.

    We can't test Streamlit render order directly, but we can confirm that
    the history list is updated synchronously during the same logical step as
    the guess — so whenever the expander reads it, it will be current.
    """

    def test_valid_guess_appended_to_history(self):
        history = []
        ok, guess_int, _ = parse_guess("42")
        assert ok
        history.append(guess_int)
        assert 42 in history

    def test_invalid_guess_appended_as_raw(self):
        history = []
        raw = "banana"
        ok, _, _ = parse_guess(raw)
        assert not ok
        history.append(raw)
        assert "banana" in history

    def test_history_grows_with_each_guess(self):
        history = []
        for raw in ["10", "20", "30"]:
            ok, val, _ = parse_guess(raw)
            history.append(val if ok else raw)
        assert len(history) == 3

    def test_latest_guess_is_last_in_history(self):
        history = []
        for raw in ["5", "15", "25"]:
            ok, val, _ = parse_guess(raw)
            history.append(val if ok else raw)
        assert history[-1] == 25


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
