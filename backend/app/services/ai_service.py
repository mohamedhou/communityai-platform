from __future__ import annotations

import re

from app.ai.base import AIProvider, AIProviderResult
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import get_settings
from app.schemas.ai import (
    AIAction,
    AIAdaptPlatformRequest,
    AIChangeToneRequest,
    AIExpandRequest,
    AIGenerateRequest,
    AIIdeasRequest,
    AIImproveRequest,
    AIPlatform,
    AIResponse,
    AIRewriteRequest,
    AIShortenRequest,
    AITone,
    AIUsage,
)


class AIService:
    def __init__(self, provider: AIProvider | None = None):
        if provider is not None:
            self.provider = provider
        else:
            settings = get_settings()
            provider_name = (settings.ai_provider or "mock").lower().strip()
            if provider_name == "openai":
                self.provider = OpenAIProvider()
            elif provider_name == "gemini":
                self.provider = GeminiProvider()
            else:
                self.provider = MockAIProvider()

    def _build_system_prompt(
        self,
        platform: AIPlatform | None = None,
        tone: AITone | None = None,
        editorial_context: str | None = None,
        action_instruction: str | None = None,
    ) -> str:
        instructions = [
            "You are an expert Social Media Copywriter and Community Strategist.",
            "Generate clean, ready-to-publish social media copy without markdown meta-chatter.",
        ]

        if platform:
            if platform == AIPlatform.LINKEDIN:
                instructions.append(
                    "Platform: LinkedIn. Use a compelling hook on the first two lines, concise paragraphs with line breaks, value-driven takeaways, and 2-4 professional hashtags."
                )
            elif platform == AIPlatform.INSTAGRAM:
                instructions.append(
                    "Platform: Instagram. Use engaging storytelling, tasteful emojis for visual pacing, a clear call-to-action (CTA), and 5-8 relevant hashtags."
                )
            elif platform == AIPlatform.FACEBOOK:
                instructions.append(
                    "Platform: Facebook. Use a conversational, community-first tone that invites comments and discussions, with 1-3 hashtags."
                )

        if tone:
            tone_descriptions = {
                AITone.FORMAL: "Tone: Formal, authoritative, precise, and polite.",
                AITone.PROFESSIONAL: "Tone: Professional, articulate, credible, and polished.",
                AITone.CASUAL: "Tone: Casual, natural, relatable, and approachable.",
                AITone.FRIENDLY: "Tone: Warm, enthusiastic, welcoming, and friendly.",
                AITone.TECHNICAL: "Tone: Technical, detailed, analytical, and informative.",
                AITone.PROMOTIONAL: "Tone: Persuasive, action-oriented, exciting, and promotional.",
            }
            if tone in tone_descriptions:
                instructions.append(tone_descriptions[tone])

        if editorial_context:
            instructions.append(f"Brand Editorial Guidelines:\n{editorial_context.strip()}")

        if action_instruction:
            instructions.append(f"Task Instruction:\n{action_instruction.strip()}")

        return "\n\n".join(instructions)

    def _to_response(self, result: AIProviderResult, action: AIAction, parse_ideas: bool = False) -> AIResponse:
        usage = None
        if result.prompt_tokens is not None or result.completion_tokens is not None:
            usage = AIUsage(
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
            )

        ideas_list = None
        if parse_ideas and result.content:
            # Extract lines starting with numbers or bullet points
            raw_lines = [line.strip() for line in result.content.split("\n") if line.strip()]
            extracted = []
            for line in raw_lines:
                clean_line = re.sub(r"^(\d+[\.\)]|\-|\*|•)\s*", "", line).strip()
                if clean_line:
                    extracted.append(clean_line)
            ideas_list = extracted if extracted else None

        return AIResponse(
            content=result.content,
            action=action,
            usage=usage,
            ideas=ideas_list,
        )

    def generate_post(self, req: AIGenerateRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            tone=req.tone,
            editorial_context=req.editorial_context,
            action_instruction="Create a new, highly engaging social media publication based on the user's prompt.",
        )

        user_prompt_parts = [f"Topic / Prompt:\n{req.prompt.strip()}"]
        if req.audience:
            user_prompt_parts.append(f"Target Audience: {req.audience.strip()}")
        if req.objective:
            user_prompt_parts.append(f"Primary Objective: {req.objective.strip()}")

        user_prompt = "\n".join(user_prompt_parts)
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.GENERATE)

    def rewrite_content(self, req: AIRewriteRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            tone=req.tone,
            editorial_context=req.editorial_context,
            action_instruction="Rewrite the provided text to make it fresh and engaging while preserving its core message.",
        )
        user_prompt = f"Please rewrite the following content:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.REWRITE)

    def improve_content(self, req: AIImproveRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            editorial_context=req.editorial_context,
            action_instruction="Enhance clarity, hook, flow, engagement, and vocabulary of the text.",
        )
        user_prompt = f"Please improve the following publication:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.IMPROVE)

    def shorten_content(self, req: AIShortenRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            editorial_context=req.editorial_context,
            action_instruction="Make the text concise and punchy while keeping the key takeaway.",
        )
        user_prompt = f"Please shorten and condense the following text:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.SHORTEN)

    def expand_content(self, req: AIExpandRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            editorial_context=req.editorial_context,
            action_instruction="Elaborate on the key points, add descriptive detail, structured takeaways or bullet points, and an inviting call-to-action.",
        )
        user_prompt = f"Please expand and elaborate on the following text:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.EXPAND)

    def change_tone(self, req: AIChangeToneRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            tone=req.tone,
            editorial_context=req.editorial_context,
            action_instruction=f"Adapt and transform the voice and phrasing of the text strictly into the {req.tone} tone.",
        )
        user_prompt = f"Please rewrite this text in a {req.tone} tone:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.CHANGE_TONE)

    def adapt_platform(self, req: AIAdaptPlatformRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            tone=req.tone,
            editorial_context=req.editorial_context,
            action_instruction=f"Format and adapt the publication specifically tailored to the culture, formatting, length, and hashtag conventions of {req.platform}.",
        )
        user_prompt = f"Please adapt this content for {req.platform}:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.ADAPT_PLATFORM)

    def generate_ideas(self, req: AIIdeasRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            tone=req.tone,
            editorial_context=req.editorial_context,
            action_instruction="Generate 4 to 5 unique, creative, and actionable publication ideas with hooks and brief concepts.",
        )

        user_prompt_parts = [f"Brainstorm social media content ideas for the following topic:\n{req.topic.strip()}"]
        if req.target_audience:
            user_prompt_parts.append(f"Target Audience: {req.target_audience.strip()}")

        user_prompt = "\n".join(user_prompt_parts)
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.IDEATE, parse_ideas=True)
