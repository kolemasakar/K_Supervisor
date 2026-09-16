from __future__ import annotations

from factory.contracts import BootstrapFile

from .chatgpt_plugin import ChatGPTPluginPreparationProfile
from .gpt_store import GPTStorePreparationProfile


class GenericReleasePreparationProfile:
    def __init__(self, target_type: str):
        self.target_type = target_type.upper()
        self._slug = self.target_type.lower().replace("_", "-")

    def generate(self, spec, release, target) -> tuple[BootstrapFile, ...]:
        path = f"release/{self._slug}/RELEASE_CHECKLIST.md"
        content = (
            f"# {self.target_type} Release Checklist\n\n"
            f"Project: {spec.name}\n\n"
            f"Release: {release.version}\n\n"
            "- [x] Generic release readiness checks passed.\n"
            "- [ ] Owner reviews target-specific publication requirements.\n"
            "- [ ] Owner performs publication when required.\n"
            "- [ ] Publication is confirmed back to K_Supervisor.\n"
        )
        return (BootstrapFile(path, content),)

    def validate(self, files: tuple[str, ...]) -> tuple[str, ...]:
        path = f"release/{self._slug}/RELEASE_CHECKLIST.md"
        return () if path in set(files) else (path,)

    @property
    def checklist(self) -> tuple[str, ...]:
        return (
            "review_target_specific_requirements",
            "perform_owner_publication_if_required",
            "confirm_publication_to_k_supervisor",
        )


def profile_for(target_type: str):
    if target_type.upper() == "CHATGPT_PLUGIN":
        return ChatGPTPluginPreparationProfile()
    if target_type.upper() == "GPT_STORE":
        return GPTStorePreparationProfile()
    return GenericReleasePreparationProfile(target_type)
