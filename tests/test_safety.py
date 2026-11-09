import json

import pytest

from prep.safety import URGENT_MESSAGE, red_flags


def test_flags_worst_headache():
    assert red_flags("Worst headache of my life today") == ["sudden severe headache"]


def test_flags_multiple_in_a_fixed_order():
    # A curly apostrophe, as phones type it.
    assert red_flags("Chest pain and I can’t breathe") == ["chest pain", "trouble breathing"]


def test_ignores_negation():
    assert red_flags("no chest pain today") == []


def test_ignores_negation_with_filler_words():
    assert red_flags("It was not the worst headache I have had") == []


@pytest.mark.parametrize(
    "text",
    [
        "no headache earlier but chest pain now",
        "No worries, chest pain right now",
        "I do not have chest pain but I cant breathe properly",
    ],
)
def test_negation_does_not_hide_a_later_flag(text):
    assert red_flags(text), text


@pytest.mark.parametrize(
    "text, flag",
    [
        ("thunderclap headache out of nowhere", "sudden severe headache"),
        ("tightness in my chest since lunch", "chest pain"),
        ("I was struggling to breathe on the stairs", "trouble breathing"),
        ("my left arm went numb and my face is drooping", "one-sided weakness or numbness"),
        ("my speech was slurred, trouble speaking", "trouble speaking"),
        ("I passed out in the kitchen", "fainting"),
        ("Felt a bit faint after standing up", "fainting"),
        ("my words came out wrong at the meeting", "trouble speaking"),
        ("I lost my vision in one eye", "sudden vision loss"),
        ("sometimes I want to hurt myself", "thoughts of self-harm"),
    ],
)
def test_each_flag_group_is_detected(text, flag):
    assert flag in red_flags(text)


def test_blurry_vision_for_a_few_minutes_is_not_a_red_flag():
    assert red_flags("Around 1pm my vision went blurry for maybe 5 minutes, then normal") == []


def test_plain_headache_is_not_a_red_flag():
    assert red_flags("Dull headache, 5/10, slept 6h, took ibuprofen") == []


def test_demo_data_has_no_flags():
    with open("data/demo_patient.json", encoding="utf-8") as f:
        notes = json.load(f)

    assert [n["created_at"] for n in notes if red_flags(n["text"])] == []


def test_urgent_message_names_the_emergency_number():
    assert "112" in URGENT_MESSAGE
