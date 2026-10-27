from app.vision.rules import evaluate
from app.vision.types import Detection

PERSON = (100, 100, 200, 400)  # 100 wide, 300 tall
HELMET_ON_HEAD = Detection("Hard_hat", 0.9, (130, 80, 170, 130))
VEST_ON_TORSO = Detection("Vest", 0.9, (110, 180, 190, 280))


def person(box=PERSON):
    return Detection("Person", 0.9, box)


def types(result):
    return sorted(v.type for v in result.violations)


def test_fully_equipped_person_is_compliant():
    result = evaluate([person(), HELMET_ON_HEAD, VEST_ON_TORSO], ["Hard_hat", "Vest"])
    assert types(result) == []
    assert result.persons[0].compliant


def test_missing_helmet_and_vest():
    result = evaluate([person()], ["Hard_hat", "Vest"])
    assert types(result) == ["NO_HARDHAT", "NO_VEST"]
    assert result.persons[0].missing == ["Hard_hat", "Vest"]


def test_helmet_held_at_waist_does_not_count():
    helmet_in_hand = Detection("Hard_hat", 0.9, (130, 260, 170, 300))
    result = evaluate([person(), helmet_in_hand, VEST_ON_TORSO], ["Hard_hat", "Vest"])
    assert types(result) == ["NO_HARDHAT"]


def test_ppe_is_matched_to_the_right_person():
    other = (400, 100, 500, 400)
    result = evaluate([person(), person(other), HELMET_ON_HEAD], ["Hard_hat"])
    assert [p.compliant for p in result.persons] == [True, False]
    assert types(result) == ["NO_HARDHAT"]
    assert result.violations[0].box == other


def test_only_required_items_are_checked():
    result = evaluate([person(), HELMET_ON_HEAD], ["Hard_hat"])
    assert types(result) == []


def test_hazard_labels_are_violations_regardless_of_case():
    dets = [Detection("Fire", 0.8, (0, 0, 50, 50)), Detection("smoke", 0.7, (0, 0, 50, 50))]
    result = evaluate(dets, ["Hard_hat"])
    assert types(result) == ["FIRE", "SMOKE"]
    assert len(result.hazards) == 2


def test_no_people_no_violations():
    assert types(evaluate([HELMET_ON_HEAD], ["Hard_hat", "Vest"])) == []
