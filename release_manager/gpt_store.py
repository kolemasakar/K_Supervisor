from __future__ import annotations

import json

from factory.contracts import BootstrapFile


_REQUIRED_GPT_FILES = (
    "release/gpt_store/GPT_STORE_PROFILE.json",
    "release/gpt_store/GPT_INSTRUCTIONS.md",
    "release/gpt_store/GPT_STORE_LISTING.md",
    "release/gpt_store/GPT_PUBLICATION_CHECKLIST.md",
)


class GPTStorePreparationProfile:
    target_type = "GPT_STORE"

    def generate(self, spec, release, target) -> tuple[BootstrapFile, ...]:
        config = spec.release.get("gpt_store", {})
        starters = config.get("conversation_starters") or (
            f"Help me use {spec.name}.",
            f"Explain what {spec.name} can do.",
            f"Start a task with {spec.name}.",
        )
        profile = {
            "schema_version": "1.0",
            "target": self.target_type,
            "release_id": release.release_id,
            "name": config.get("name") or spec.name,
            "description": config.get("description") or spec.purpose,
            "instructions_path": "release/gpt_store/GPT_INSTRUCTIONS.md",
            "conversation_starters": list(starters),
            "knowledge_files": list(config.get("knowledge_files", ())),
            "capabilities": dict(config.get("capabilities", {})),
            "actions": list(config.get("actions", ())),
        }
        instructions = (
            f"# {profile['name']} Instructions\n\n"
            f"Purpose: {spec.purpose}\n\n"
            f"Problem: {spec.problem_statement}\n\n"
            "Success criteria:\n"
            + "\n".join(f"- {item}" for item in spec.success_criteria)
            + "\n"
        )
        listing = (
            f"# {profile['name']}\n\n"
            f"Description: {profile['description']}\n\n"
            "## Conversation Starters\n\n"
            + "\n".join(f"- {item}" for item in starters)
            + "\n"
        )
        checklist = """# GPT Store Publication Checklist

Automatically prepared:
- [x] Name and description profile generated.
- [x] Instructions asset generated.
- [x] Conversation starters generated or normalized.
- [x] Machine-readable GPT Store profile generated.

Owner publication actions:
- [ ] Review final name, description, instructions, and starters.
- [ ] Upload/configure declared knowledge files, if any.
- [ ] Configure and verify declared actions/capabilities, if any.
- [ ] Complete any applicable privacy or policy requirements.
- [ ] Publish in the GPT Store using the owner account.
- [ ] Confirm publication back to K_Supervisor.
"""
        return (
            BootstrapFile(_REQUIRED_GPT_FILES[0], json.dumps(profile, indent=2, sort_keys=True) + "\n"),
            BootstrapFile(_REQUIRED_GPT_FILES[1], instructions),
            BootstrapFile(_REQUIRED_GPT_FILES[2], listing),
            BootstrapFile(_REQUIRED_GPT_FILES[3], checklist),
        )

    def validate(self, files: tuple[str, ...]) -> tuple[str, ...]:
        available = set(files)
        return tuple(path for path in _REQUIRED_GPT_FILES if path not in available)

    @property
    def checklist(self) -> tuple[str, ...]:
        return (
            "review_generated_gpt_assets",
            "configure_declared_knowledge_and_actions",
            "complete_applicable_policy_requirements",
            "publish_with_owner_account",
            "confirm_publication_to_k_supervisor",
        )
