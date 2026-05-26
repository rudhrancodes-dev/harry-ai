"""Catalogue invariants. These tests are the contract for skill uniqueness."""
from collections import Counter

from harry.skills.handlers import HANDLERS
from harry.skills.registry import SKILLS


def test_catalogue_has_98_skills():
    assert len(SKILLS) == 98, f"expected 98 skills, got {len(SKILLS)}"


def test_skill_ids_are_unique():
    ids = [s.id for s in SKILLS]
    dupes = [k for k, v in Counter(ids).items() if v > 1]
    assert not dupes, f"duplicate skill ids: {dupes}"


def test_every_trigger_is_globally_unique():
    triggers = [t for s in SKILLS for t in s.triggers]
    dupes = [k for k, v in Counter(t.lower() for t in triggers).items() if v > 1]
    assert not dupes, f"trigger phrases collide across skills: {dupes}"


def test_every_skill_has_at_least_one_trigger():
    bad = [s.id for s in SKILLS if not s.triggers]
    assert not bad, f"skills with no triggers: {bad}"


def test_handler_skills_have_registered_handlers():
    missing = [s.id for s in SKILLS if s.handler != "llm" and s.handler not in HANDLERS]
    assert not missing, f"skills point at missing handlers: {missing}"


def test_llm_skills_have_prompts():
    empty = [s.id for s in SKILLS if s.handler == "llm" and not s.prompt]
    assert not empty, f"llm skills with no prompt: {empty}"
