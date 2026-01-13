"""Agent prompt model for AI agent configurations."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentPrompt:
    """Model representing an AI agent's prompt configuration."""
    
    name: str
    role: str
    description: str
    system_prompt: str
    example_format: dict[str, Any] = field(default_factory=dict)
    context_guidance: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "example_format": self.example_format,
            "context_guidance": self.context_guidance
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentPrompt":
        """Create an AgentPrompt from a dictionary."""
        return cls(
            name=data.get("name", ""),
            role=data.get("role", ""),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            example_format=data.get("example_format", {}),
            context_guidance=data.get("context_guidance", [])
        )
    
    def is_valid(self) -> bool:
        """Check if the prompt configuration is valid."""
        return bool(
            self.name and
            self.role and
            self.description and
            self.system_prompt and
            isinstance(self.example_format, dict) and
            isinstance(self.context_guidance, list)
        )
