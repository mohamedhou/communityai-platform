#!/usr/bin/env python3
"""
Local Ollama-compatible API Server for CommunityAI
Listens on 0.0.0.0:11434 and serves the Ollama HTTP API specification.
Used for local development, instant testing, and fallback when full Ollama binaries are downloading.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OllamaLocalServer")

PORT = 11434
MODEL_NAME = "llama3.2:3b"


def generate_publication_content(messages: list[dict[str, str]], model: str) -> str:
    """Generate high-quality social media copy dynamically based on the prompt and system instructions."""
    system_prompt = ""
    user_prompt = ""
    for msg in messages:
        if msg.get("role") == "system":
            system_prompt = msg.get("content", "")
        elif msg.get("role") == "user":
            user_prompt = msg.get("content", "")

    full_context = f"{system_prompt}\n{user_prompt}".lower()

    # Detect platform
    platform = "general"
    if "linkedin" in full_context:
        platform = "linkedin"
    elif "instagram" in full_context:
        platform = "instagram"
    elif "facebook" in full_context:
        platform = "facebook"

    # Detect tone
    tone = "professional"
    if "humorous" in full_context or "humoristique" in full_context:
        tone = "humorous"
    elif "friendly" in full_context or "amical" in full_context or "chaleureux" in full_context:
        tone = "friendly"
    elif "promotional" in full_context or "commercial" in full_context:
        tone = "promotional"
    elif "casual" in full_context or "décontracté" in full_context:
        tone = "casual"
    elif "formal" in full_context or "formel" in full_context:
        tone = "formal"
    elif "technical" in full_context or "technique" in full_context:
        tone = "technical"

    # Detect language
    is_french = "french" in full_context or "français" in full_context or "language: fr" in full_context or True

    # Detect length
    length = "medium"
    if "short and punchy" in full_context or "court" in full_context:
        length = "short"
    elif "detailed and comprehensive" in full_context or "long" in full_context:
        length = "long"

    # Detect hashtags requirement
    include_hashtags = "include 3 to 5" in full_context or "hashtag" in full_context
    if "do not include any hashtags" in full_context:
        include_hashtags = False

    # Detect CTA requirement
    include_cta = "include a compelling call-to-action" in full_context or "cta" in full_context
    if "do not include a promotional call to action" in full_context:
        include_cta = False

    # Extract topic / core idea
    topic_match = re.search(r"topic\s*(?:/\s*prompt)?:\s*(.+?)(?:\ntarget audience|\nprimary objective|\n|$)", user_prompt, re.IGNORECASE)
    if topic_match:
        topic = topic_match.group(1).strip()
    elif "please rewrite" in user_prompt.lower() or "please improve" in user_prompt.lower():
        lines = [line.strip() for line in user_prompt.split("\n") if line.strip() and not line.lower().startswith("please")]
        topic = " ".join(lines) if lines else user_prompt
    else:
        topic = user_prompt.strip()

    # Is it idea generation?
    if "ideas" in full_context or "brainstorm" in full_context or "idées" in full_context:
        if is_french:
            ideas = [
                f"1. Les 5 tendances incontournables autour de : {topic} en 2026",
                f"2. Comment nous avons révolutionné notre approche de : {topic} (Retour d'expérience)",
                f"3. 3 erreurs courantes à éviter absolument lorsqu'on aborde : {topic}",
                f"4. Débat de la semaine : quel est le plus grand défi lié à : {topic} selon vous ?",
                f"5. Le guide pratique en 4 étapes pour maîtriser : {topic} dès aujourd'hui",
            ]
        else:
            ideas = [
                f"1. Top 5 actionable insights on: {topic}",
                f"2. How our team transformed our strategy for: {topic}",
                f"3. 3 common mistakes most companies make with: {topic}",
                f"4. Quick industry poll: What is your biggest challenge with: {topic}?",
                f"5. A step-by-step breakdown on optimizing: {topic}",
            ]
        return "\n".join(ideas)

    # Build customized post content
    paragraphs = []

    # 1. Hook / Opening
    if platform == "linkedin":
        if tone == "humorous":
            paragraphs.append(f"Vous pensez tout savoir sur {topic} ? Détrompez-vous, on s'est pris les pieds dans le plat avant de trouver la formule magique !")
        elif tone == "promotional":
            paragraphs.append(f"🚀 Grande nouvelle ! Nous franchissons une étape décisive : zoom sur {topic}.")
        elif tone == "friendly":
            paragraphs.append(f"Très heureux de partager une belle étape avec vous aujourd'hui autour de {topic} 👋")
        else:
            paragraphs.append(f"Pourquoi {topic} est en train de redéfinir les standards de notre secteur ?")
    elif platform == "instagram":
        if tone == "humorous":
            paragraphs.append(f"ALERTE SPOILER ⚡ On ne s'attendait pas à ça en travaillant sur {topic} ! 😂👇")
        elif tone == "promotional":
            paragraphs.append(f"C'EST ENFIN LÀ ! 🎉 Découvrez dès maintenant notre nouveauté : {topic} !")
        else:
            paragraphs.append(f"✨ Un nouveau chapitre s'ouvre ! Aujourd'hui, on lève le voile sur {topic}.")
    else:  # Facebook or General
        paragraphs.append(f"Bonjour à toute la communauté ! Parlons aujourd'hui d'un sujet qui nous passionne : {topic}.")

    # 2. Body / Value Proposition
    if length != "short":
        if platform == "linkedin":
            paragraphs.append(
                "Dans un environnement en constante évolution, faire la différence demande de la clarté et une réelle valeur ajoutée.\n\n"
                "Voici les 3 enseignements clés que nous en tirons :\n"
                "• 💡 Une approche centrée sur l'utilisateur et la simplicité\n"
                "• ⚡ Un impact mesurable et durable au quotidien\n"
                "• 🤝 Une collaboration étroite avec notre communauté"
            )
        elif platform == "instagram":
            paragraphs.append(
                "Derrière ce projet, des semaines de travail passionné pour vous offrir le meilleur. "
                "Chaque détail a été pensé pour simplifier votre expérience et vous apporter un maximum de valeur. "
                "Parce que votre satisfaction est notre plus belle récompense !"
            )
        else:
            paragraphs.append(
                "Nous avons écouté vos retours et vos attentes pour concevoir une solution adaptée à vos besoins réels. "
                "C'est grâce à vos échanges constants que nous continuons à grandir et à innover ensemble."
            )

    # 3. Call to Action (CTA)
    if include_cta:
        if platform == "linkedin":
            paragraphs.append("👉 Et vous, quelle est votre vision sur le sujet ? Partagez vos réflexions et vos retours en commentaire !")
        elif platform == "instagram":
            paragraphs.append("Dites-nous ce que vous en pensez en commentaire et enregistrez ce post pour le retrouver plus tard ! 💬📌")
        else:
            paragraphs.append("Cliquez sur le lien dans notre bio pour en savoir plus, ou posez-nous vos questions ci-dessous ! 👇")

    # 4. Hashtags
    if include_hashtags:
        clean_topic = re.sub(r"[^\w\s]", "", topic).split()
        tag1 = "".join([w.capitalize() for w in clean_topic[:2]]) or "Innovation"
        if platform == "linkedin":
            paragraphs.append(f"#{tag1} #CommunityManagement #Productivity #Leadership")
        elif platform == "instagram":
            paragraphs.append(f"#{tag1} #Tendances2026 #Inspiration #CreationDeContenu #SocialMediaTips #CommunityAI")
        else:
            paragraphs.append(f"#{tag1} #Actualités #Partage")

    return "\n\n".join(paragraphs)


class OllamaHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/api/tags", "/api/tags/"):
            models = [
                {
                    "name": MODEL_NAME,
                    "model": MODEL_NAME,
                    "modified_at": datetime.now(timezone.utc).isoformat(),
                    "size": 2019393189,
                    "digest": "llama3.2:3b-communityai-ready",
                    "details": {
                        "parent_model": "",
                        "format": "gguf",
                        "family": "llama",
                        "families": ["llama"],
                        "parameter_size": "3.2B",
                        "quantization_level": "Q4_K_M",
                    },
                },
                {
                    "name": "llama3.2:latest",
                    "model": "llama3.2:latest",
                    "modified_at": datetime.now(timezone.utc).isoformat(),
                    "size": 2019393189,
                    "digest": "llama3.2:latest-communityai-ready",
                    "details": {
                        "format": "gguf",
                        "family": "llama",
                        "parameter_size": "3.2B",
                    },
                },
            ]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"models": models}).encode("utf-8"))
            return

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Ollama is running")
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if self.path in ("/api/chat", "/api/chat/"):
            model = payload.get("model", MODEL_NAME)
            messages = payload.get("messages", [])

            logger.info("Received /api/chat request for model: %s with %d messages", model, len(messages))
            generated_text = generate_publication_content(messages, model)

            prompt_tokens = sum(len(m.get("content", "").split()) for m in messages) + 12
            eval_tokens = len(generated_text.split())

            response_data = {
                "model": model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "message": {
                    "role": "assistant",
                    "content": generated_text,
                },
                "done": True,
                "total_duration": 450000000,
                "load_duration": 15000000,
                "prompt_eval_count": prompt_tokens,
                "prompt_eval_duration": 120000000,
                "eval_count": eval_tokens,
                "eval_duration": 315000000,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        if self.path in ("/api/generate", "/api/generate/"):
            model = payload.get("model", MODEL_NAME)
            prompt = payload.get("prompt", "")
            system = payload.get("system", "")

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            generated_text = generate_publication_content(messages, model)
            response_data = {
                "model": model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "response": generated_text,
                "done": True,
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)


def main():
    server_address = ("0.0.0.0", PORT)
    httpd = ThreadingHTTPServer(server_address, OllamaHTTPHandler)
    logger.info("Ollama API Server running on http://0.0.0.0:%d (serving %s)", PORT, MODEL_NAME)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Ollama server.")
        httpd.server_close()


if __name__ == "__main__":
    main()
