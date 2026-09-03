from __future__ import annotations

from app.ai.base import AIProvider, AIProviderResult


class MockAIProvider(AIProvider):
    """Deterministic Mock AI Provider for tests and offline development."""

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        prompt_lower = prompt.lower()
        sys_lower = (system_prompt or "").lower()

        if "idea" in prompt_lower or "ideate" in sys_lower:
            content = (
                "1. 🚀 Behind-the-scenes look at our newest product launch.\n"
                "2. 💡 3 Key lessons learned while scaling our community platform.\n"
                "3. 📊 Customer spotlight: How Company X achieved a 40% growth in engagement.\n"
                "4. ❓ Interactive poll: What is your #1 productivity blocker this quarter?\n"
                "5. 🎯 Expert tip of the week: Optimizing your social workflow with AI."
            )
        elif "shorten" in sys_lower or "raccourcir" in sys_lower or "shorten" in prompt_lower:
            content = "Exciting news! Our new AI feature is live. Try it today and scale your workflow. 🚀"
        elif "expand" in sys_lower or "développer" in sys_lower or "expand" in prompt_lower:
            content = (
                "We are thrilled to announce the official release of our next-generation platform updates! 🚀\n\n"
                "Here is what is new:\n"
                "• Seamless multi-channel scheduling\n"
                "• Built-in AI copywriting & ideation assistant\n"
                "• Advanced analytics & performance insights\n\n"
                "What feature are you most excited to explore? Drop your thoughts below! 👇"
            )
        elif "rewrite" in sys_lower or "reformuler" in sys_lower:
            content = "Discover our latest innovations designed to elevate your social media strategy with ease and precision."
        elif "improve" in sys_lower or "améliorer" in sys_lower:
            content = "Unlock the power of automated scheduling and creative AI tools to boost your brand's online presence. ✨"
        elif "tone" in sys_lower or "ton" in sys_lower:
            content = "We are proud to present our enhanced social management suite, crafted to deliver optimal operational efficiency."
        elif "platform" in sys_lower or "linkedin" in prompt_lower or "instagram" in prompt_lower:
            content = (
                "Transform the way you manage social communities! 🌟\n\n"
                "Connect with your audience seamlessly across Meta and LinkedIn with AI-powered publishing.\n\n"
                "#CommunityAI #SocialMedia #Productivity #AI"
            )
        else:
            content = (
                "Ready to take your social media to the next level? 🚀\n\n"
                "Discover how CommunityAI streamlines your content workflow from drafting to publishing.\n\n"
                "#Innovation #SocialStrategy #CommunityAI"
            )

        prompt_tokens = len(prompt.split()) + len((system_prompt or "").split())
        completion_tokens = len(content.split())

        return AIProviderResult(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
