from __future__ import annotations

import re

from app.ai.base import AIProvider, AIProviderResult
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.ollama import OllamaProvider
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
    AIProviderStatusResponse,
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
            if provider_name == "ollama":
                self.provider = OllamaProvider()
            elif provider_name == "openai":
                self.provider = OpenAIProvider()
            elif provider_name == "gemini":
                self.provider = GeminiProvider()
            else:
                self.provider = MockAIProvider()

    def get_status(self) -> AIProviderStatusResponse:
        settings = get_settings()
        provider_name = (settings.ai_provider or "mock").lower().strip()

        if isinstance(self.provider, OllamaProvider):
            info = self.provider.check_availability()
            return AIProviderStatusResponse(
                provider="ollama",
                model=self.provider.model,
                available=info.get("available", False),
                base_url=self.provider.base_url,
                error=info.get("error"),
                installed_models=info.get("installed_models", []),
            )
        elif isinstance(self.provider, OpenAIProvider):
            has_key = bool(self.provider.api_key)
            return AIProviderStatusResponse(
                provider="openai",
                model=self.provider.model,
                available=has_key,
                error=None if has_key else "OpenAI API key is missing",
            )
        elif isinstance(self.provider, GeminiProvider):
            has_key = bool(self.provider.api_key)
            return AIProviderStatusResponse(
                provider="gemini",
                model=self.provider.model,
                available=has_key,
                error=None if has_key else "Gemini API key is missing",
            )
        elif isinstance(self.provider, MockAIProvider):
            return AIProviderStatusResponse(
                provider="mock",
                model="deterministic-mock",
                available=True,
            )
        else:
            return AIProviderStatusResponse(
                provider=provider_name,
                model="unknown",
                available=True,
            )

    def _build_system_prompt(
        self,
        platform: AIPlatform | None = None,
        tone: AITone | None = None,
        editorial_context: str | None = None,
        action_instruction: str | None = None,
        language: str | None = None,
        length: str | None = None,
        include_hashtags: bool | None = None,
        include_cta: bool | None = None,
    ) -> str:
        instructions = [
            "You are an expert Social Media Copywriter and Community Strategist.",
            "Generate clean, ready-to-publish social media copy without markdown meta-chatter.",
        ]

        # Language constraint
        lang = (language or "fr").lower().strip()
        if lang in {"fr", "french", "français"}:
            instructions.append(
                "Language: Rédige impérativement le contenu en Français naturel, fluide et percutant."
            )
        elif lang in {"en", "english"}:
            instructions.append(
                "Language: Write strictly in natural, engaging English."
            )
        elif lang:
            instructions.append(f"Language: Write strictly in {lang}.")

        # Platform formatting
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

        # Tone of voice
        if tone:
            tone_descriptions = {
                AITone.FORMAL: "Tone: Formal, authoritative, precise, and polite.",
                AITone.PROFESSIONAL: "Tone: Professional, articulate, credible, and polished.",
                AITone.CASUAL: "Tone: Casual, natural, relatable, and approachable.",
                AITone.FRIENDLY: "Tone: Warm, enthusiastic, welcoming, and friendly.",
                AITone.TECHNICAL: "Tone: Technical, detailed, analytical, and informative.",
                AITone.PROMOTIONAL: "Tone: Persuasive, action-oriented, exciting, and commercial.",
                AITone.HUMOROUS: "Tone: Humorous, witty, playful, and entertaining.",
            }
            if tone in tone_descriptions:
                instructions.append(tone_descriptions[tone])

        # Length preference
        if length:
            len_lower = length.lower().strip()
            if len_lower in {"short", "court"}:
                instructions.append("Length: Short and punchy (1 to 3 sentences maximum).")
            elif len_lower in {"medium", "moyen"}:
                instructions.append("Length: Medium (1 to 2 well-structured paragraphs).")
            elif len_lower in {"long"}:
                instructions.append("Length: Detailed and comprehensive with bullet points and full narrative.")

        # Hashtags
        if include_hashtags is True:
            instructions.append("Hashtags: Include 3 to 5 highly relevant hashtags at the very end.")
        elif include_hashtags is False:
            instructions.append("Hashtags: Do NOT include any hashtags.")

        # Call to Action
        if include_cta is True:
            instructions.append("Call to Action: Include a compelling call-to-action (CTA) prompting user interaction or next steps.")
        elif include_cta is False:
            instructions.append("Call to Action: Do NOT include a promotional call to action.")

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
            language=req.language,
            length=req.length,
            include_hashtags=req.include_hashtags,
            include_cta=req.include_cta,
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
            language=req.language,
            include_hashtags=req.include_hashtags,
            include_cta=req.include_cta,
        )
        user_prompt = f"Please rewrite the following content:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.REWRITE)

    def improve_content(self, req: AIImproveRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            editorial_context=req.editorial_context,
            action_instruction="Enhance clarity, hook, flow, engagement, and vocabulary of the text.",
            language=req.language,
            include_hashtags=req.include_hashtags,
            include_cta=req.include_cta,
        )
        user_prompt = f"Please improve the following publication:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.IMPROVE)

    def shorten_content(self, req: AIShortenRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            editorial_context=req.editorial_context,
            action_instruction="Make the text concise and punchy while keeping the key takeaway.",
            language=req.language,
            length="short",
        )
        user_prompt = f"Please shorten and condense the following text:\n\n{req.content.strip()}"
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.SHORTEN)

    def expand_content(self, req: AIExpandRequest) -> AIResponse:
        sys_prompt = self._build_system_prompt(
            platform=req.platform,
            editorial_context=req.editorial_context,
            action_instruction="Elaborate on the key points, add descriptive detail, structured takeaways or bullet points, and an inviting call-to-action.",
            language=req.language,
            length="long",
            include_hashtags=req.include_hashtags,
            include_cta=req.include_cta,
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
            language=req.language,
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
            language=req.language,
            include_hashtags=req.include_hashtags,
            include_cta=req.include_cta,
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
            language=req.language,
        )

        user_prompt_parts = [f"Brainstorm social media content ideas for the following topic:\n{req.topic.strip()}"]
        if req.target_audience:
            user_prompt_parts.append(f"Target Audience: {req.target_audience.strip()}")

        user_prompt = "\n".join(user_prompt_parts)
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.IDEATE, parse_ideas=True)

    def suggest_reply(
        self,
        content: str,
        interaction_type: str,
        platform: str,
        sender_name: str,
        sentiment: str,
        tone: AITone | None = None,
        instructions: str | None = None,
    ) -> AIResponse:
        tone_val = tone or AITone.FRIENDLY
        sys_prompt = self._build_system_prompt(
            platform=None,
            tone=tone_val,
            action_instruction=(
                f"You are an expert Community Manager replying to a social interaction on {platform}. "
                f"The message is a {interaction_type} with {sentiment} sentiment from user {sender_name}. "
                "Draft a professional, empathetic, and engaging reply ready to send directly to the user."
            ),
            language="fr",
        )

        user_prompt_parts = [
            f"Sender: {sender_name}",
            f"Platform: {platform}",
            f"Type: {interaction_type}",
            f"Sentiment: {sentiment}",
            f"Original Message:\n{content.strip()}",
        ]
        if instructions:
            user_prompt_parts.append(f"Additional Instructions: {instructions.strip()}")

        user_prompt = "\n\n".join(user_prompt_parts)
        result = self.provider.generate(prompt=user_prompt, system_prompt=sys_prompt)
        return self._to_response(result, AIAction.SUGGEST_REPLY)
