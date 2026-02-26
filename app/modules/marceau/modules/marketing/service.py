"""
AZALS MODULE - Marceau Marketing Service
=========================================

Service de marketing automatise.
Integration avec les reseaux sociaux et le module email.

Actions:
- create_campaign: Creation campagne marketing
- post_social: Publication reseaux sociaux
- send_newsletter: Envoi newsletter
- analyze_performance: Analyse performances
"""
from __future__ import annotations


import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.modules.marceau.models import ActionStatus, MarceauAction, MarceauMemory, MemoryType, ModuleName

logger = logging.getLogger(__name__)


class MarketingService:
    """
    Service marketing Marceau.
    Gere les campagnes, reseaux sociaux, emailing.
    """

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db

    async def execute_action(
        self,
        action: str,
        data: dict,
        context: list[str]
    ) -> dict:
        """Execute une action marketing."""
        action_handlers = {
            "create_campaign": self._create_campaign,
            "post_social": self._post_social,
            "send_newsletter": self._send_newsletter,
            "analyze_performance": self._analyze_performance,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    # =========================================================================
    # CREATE CAMPAIGN
    # =========================================================================

    async def _create_campaign(self, data: dict, context: list[str]) -> dict:
        """
        Cree une campagne marketing.

        Args:
            data: {
                "name": str (obligatoire)
                "type": str (email|social|multi)
                "objective": str (awareness|engagement|conversion)
                "target_audience": str (optionnel)
                "content": str (optionnel - genere par LLM si absent)
                "start_date": str (ISO date, optionnel)
                "end_date": str (ISO date, optionnel)
                "budget": float (optionnel)
                "channels": list[str] (facebook|linkedin|instagram|email)
            }

        Returns:
            Campagne creee avec campaign_id
        """
        try:
            # Validation
            if not data.get("name"):
                return {
                    "success": False,
                    "error": "name obligatoire",
                    "module": "marketing"
                }

            campaign_type = data.get("type", "multi")
            objective = data.get("objective", "engagement")
            channels = data.get("channels", ["email"])

            # Generer le contenu si non fourni
            content = data.get("content")
            if not content:
                content = await self._generate_campaign_content(
                    name=data["name"],
                    objective=objective,
                    audience=data.get("target_audience", "clients"),
                    context=context
                )

            # Stocker la campagne en memoire (en attendant un modele dedie)
            campaign_id = uuid.uuid4()

            campaign_data = {
                "id": str(campaign_id),
                "name": data["name"],
                "type": campaign_type,
                "objective": objective,
                "target_audience": data.get("target_audience"),
                "content": content,
                "channels": channels,
                "start_date": data.get("start_date") or datetime.utcnow().isoformat(),
                "end_date": data.get("end_date"),
                "budget": data.get("budget"),
                "status": "draft",
                "metrics": {
                    "impressions": 0,
                    "clicks": 0,
                    "conversions": 0,
                }
            }

            # Stocker en memoire Marceau
            memory = MarceauMemory(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                memory_type=MemoryType.KNOWLEDGE,
                content=f"Campagne {data['name']}: {content[:500]}",
                tags=["campaign", campaign_type, objective],
                importance_score=0.6,
                metadata=campaign_data,
            )
            self.db.add(memory)

            # Action Marceau
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.MARKETING,
                action_type="campaign_created",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data=campaign_data,
                confidence_score=0.9,
            )
            self.db.add(action)
            self.db.commit()

            logger.info(f"[MARCEAU] Campagne {data['name']} creee")

            return {
                "success": True,
                "campaign_id": str(campaign_id),
                "name": data["name"],
                "type": campaign_type,
                "channels": channels,
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "action_id": str(action.id),
                "message": f"Campagne '{data['name']}' creee avec succes",
                "module": "marketing"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur creation campagne: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "marketing"
            }

    async def _generate_campaign_content(
        self, name: str, objective: str, audience: str, context: list[str]
    ) -> str:
        """Genere le contenu d'une campagne via LLM."""
        try:
            from app.modules.marceau.llm_client import get_llm_client_for_tenant

            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""
Genere le contenu pour une campagne marketing.

Nom: {name}
Objectif: {objective} (awareness=notoriete, engagement=interaction, conversion=vente)
Audience cible: {audience}

Contexte entreprise:
{chr(10).join(context[:2]) if context else "AZALSCORE - ERP decisional pour PME/ETI"}

Genere:
1. Un titre accrocheur (max 60 caracteres)
2. Un texte principal (max 150 mots)
3. Un call-to-action

Format:
TITRE: ...
TEXTE: ...
CTA: ...
"""

            response = await llm.generate(prompt, temperature=0.8, max_tokens=400)
            return response

        except Exception as e:
            logger.warning(f"[MARCEAU] LLM indisponible: {e}")
            return f"""
TITRE: {name}

TEXTE: Decouvrez comment ameliorer votre gestion d'entreprise avec notre solution.
Nos clients gagnent en moyenne 30% de productivite grace a notre cockpit decisional.

CTA: Demandez votre demo gratuite
"""

    # =========================================================================
    # POST SOCIAL
    # =========================================================================

    async def _post_social(self, data: dict, context: list[str]) -> dict:
        """
        Publie sur les reseaux sociaux.

        Args:
            data: {
                "platform": str (facebook|linkedin|instagram)
                "content": str (obligatoire)
                "image_url": str (optionnel)
                "link": str (optionnel)
                "schedule_at": str (ISO datetime, optionnel)
            }

        Returns:
            Confirmation de publication avec post_id
        """
        try:
            from app.modules.marceau.config import get_or_create_marceau_config

            platform = data.get("platform")
            content = data.get("content")

            if not platform or not content:
                return {
                    "success": False,
                    "error": "platform et content obligatoires",
                    "module": "marketing"
                }

            # Recuperer les credentials
            config = get_or_create_marceau_config(self.tenant_id, self.db)
            integrations = config.integrations or {}

            token_key = f"{platform}_token"
            token = integrations.get(token_key)

            if not token:
                return {
                    "success": False,
                    "error": f"Token {platform} non configure. Configurez-le dans Administration > Marceau > Integrations.",
                    "module": "marketing"
                }

            # Publication selon la plateforme
            result = None
            if platform == "facebook":
                result = await self._post_to_facebook(token, content, data)
            elif platform == "linkedin":
                result = await self._post_to_linkedin(token, content, data)
            elif platform == "instagram":
                result = await self._post_to_instagram(token, content, data)
            else:
                return {
                    "success": False,
                    "error": f"Plateforme {platform} non supportee",
                    "available_platforms": ["facebook", "linkedin", "instagram"],
                    "module": "marketing"
                }

            if result.get("success"):
                # Action Marceau
                action = MarceauAction(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    module=ModuleName.MARKETING,
                    action_type="social_post",
                    status=ActionStatus.COMPLETED,
                    input_data=data,
                    output_data=result,
                    confidence_score=1.0,
                )
                self.db.add(action)
                self.db.commit()

                logger.info(f"[MARCEAU] Post {platform} publie: {result.get('post_id')}")

            return result

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur publication sociale: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "marketing"
            }

    async def _post_to_facebook(self, token: str, content: str, data: dict) -> dict:
        """Publie sur Facebook."""
        import httpx

        try:
            payload = {
                "message": content,
                "access_token": token,
            }

            if data.get("link"):
                payload["link"] = data["link"]

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://graph.facebook.com/v18.0/me/feed",
                    data=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "platform": "facebook",
                        "post_id": result.get("id"),
                        "message": "Post Facebook publie",
                        "module": "marketing"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Facebook API error: {response.text[:200]}",
                        "module": "marketing"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Facebook error: {str(e)}",
                "module": "marketing"
            }

    async def _post_to_linkedin(self, token: str, content: str, data: dict) -> dict:
        """Publie sur LinkedIn."""
        import httpx

        try:
            # D'abord recuperer l'ID utilisateur
            async with httpx.AsyncClient(timeout=30.0) as client:
                me_response = await client.get(
                    "https://api.linkedin.com/v2/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if me_response.status_code != 200:
                    return {
                        "success": False,
                        "error": "Impossible de recuperer le profil LinkedIn",
                        "module": "marketing"
                    }

                user_id = me_response.json().get("id")

                # Creer le post
                post_data = {
                    "author": f"urn:li:person:{user_id}",
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": content},
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }

                if data.get("link"):
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                        "status": "READY",
                        "originalUrl": data["link"],
                    }]

                response = await client.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0",
                    },
                    json=post_data
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        "success": True,
                        "platform": "linkedin",
                        "post_id": result.get("id"),
                        "message": "Post LinkedIn publie",
                        "module": "marketing"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"LinkedIn API error: {response.text[:200]}",
                        "module": "marketing"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"LinkedIn error: {str(e)}",
                "module": "marketing"
            }

    async def _post_to_instagram(self, token: str, content: str, data: dict) -> dict:
        """Publie sur Instagram (necessite une image)."""
        import httpx

        image_url = data.get("image_url")
        if not image_url:
            return {
                "success": False,
                "error": "Instagram requiert une image (image_url)",
                "module": "marketing"
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Etape 1: Creer le container media
                container_response = await client.post(
                    "https://graph.facebook.com/v18.0/me/media",
                    data={
                        "image_url": image_url,
                        "caption": content,
                        "access_token": token,
                    }
                )

                if container_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Instagram container error: {container_response.text[:200]}",
                        "module": "marketing"
                    }

                container_id = container_response.json().get("id")

                # Etape 2: Publier le container
                publish_response = await client.post(
                    "https://graph.facebook.com/v18.0/me/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": token,
                    }
                )

                if publish_response.status_code == 200:
                    result = publish_response.json()
                    return {
                        "success": True,
                        "platform": "instagram",
                        "post_id": result.get("id"),
                        "message": "Post Instagram publie",
                        "module": "marketing"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Instagram publish error: {publish_response.text[:200]}",
                        "module": "marketing"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Instagram error: {str(e)}",
                "module": "marketing"
            }

    # =========================================================================
    # SEND NEWSLETTER
    # =========================================================================

    async def _send_newsletter(self, data: dict, context: list[str]) -> dict:
        """
        Envoie une newsletter.

        Args:
            data: {
                "subject": str (obligatoire)
                "content": str (obligatoire si pas generate)
                "generate_content": bool (defaut: False)
                "topic": str (requis si generate_content)
                "segment": str (all|customers|prospects|vip)
                "schedule_at": str (ISO datetime, optionnel)
            }

        Returns:
            Statistiques d'envoi
        """
        try:
            from app.modules.email.service import EmailService
            from app.modules.commercial.models import Customer, CustomerType

            subject = data.get("subject")
            if not subject:
                return {
                    "success": False,
                    "error": "subject obligatoire",
                    "module": "marketing"
                }

            # Generer ou recuperer le contenu
            content = data.get("content")
            if data.get("generate_content") and not content:
                topic = data.get("topic", "actualites")
                content = await self._generate_newsletter_content(topic, context)

            if not content:
                return {
                    "success": False,
                    "error": "content obligatoire (ou generate_content avec topic)",
                    "module": "marketing"
                }

            # Recuperer les destinataires selon le segment
            segment = data.get("segment", "all")
            recipients = await self._get_newsletter_recipients(segment)

            if not recipients:
                return {
                    "success": False,
                    "error": f"Aucun destinataire trouve pour le segment '{segment}'",
                    "module": "marketing"
                }

            # Preparer l'email HTML
            html_content = self._format_newsletter_html(subject, content)

            # Envoyer les emails
            email_service = EmailService(self.db, self.tenant_id)

            sent_count = 0
            failed_count = 0
            errors = []

            from app.modules.email.schemas import SendEmailRequest

            for recipient in recipients[:100]:  # Limite a 100 pour eviter les abus
                try:
                    request = SendEmailRequest(
                        to=recipient["email"],
                        subject=subject,
                        body_html=html_content,
                        body_text=content,
                    )

                    result = email_service.send_email(request)
                    if result.success:
                        sent_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"{recipient['email']}: {result.error}")

                except Exception as e:
                    failed_count += 1
                    errors.append(f"{recipient['email']}: {str(e)[:50]}")

            # Action Marceau
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.MARKETING,
                action_type="newsletter_sent",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "total_recipients": len(recipients),
                },
                confidence_score=1.0,
            )
            self.db.add(action)
            self.db.commit()

            logger.info(f"[MARCEAU] Newsletter envoyee: {sent_count}/{len(recipients)}")

            return {
                "success": True,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_recipients": len(recipients),
                "errors": errors[:5] if errors else None,
                "action_id": str(action.id),
                "message": f"Newsletter envoyee a {sent_count} destinataire(s)",
                "module": "marketing"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur envoi newsletter: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "marketing"
            }

    async def _get_newsletter_recipients(self, segment: str) -> list[dict]:
        """Recupere les destinataires selon le segment."""
        from app.modules.commercial.models import Customer, CustomerType

        query = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.is_active == True,
            Customer.email.isnot(None),
        )

        if segment == "customers":
            query = query.filter(Customer.type == CustomerType.CUSTOMER)
        elif segment == "prospects":
            query = query.filter(Customer.type.in_([CustomerType.PROSPECT, CustomerType.LEAD]))
        elif segment == "vip":
            query = query.filter(Customer.type == CustomerType.VIP)
        # "all" = pas de filtre supplementaire

        customers = query.all()

        return [{"email": c.email, "name": c.name} for c in customers if c.email]

    async def _generate_newsletter_content(self, topic: str, context: list[str]) -> str:
        """Genere le contenu de la newsletter."""
        try:
            from app.modules.marceau.llm_client import get_llm_client_for_tenant

            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""
Redige une newsletter professionnelle sur le sujet suivant: {topic}

Contexte entreprise:
{chr(10).join(context[:2]) if context else "AZALSCORE - Solution ERP pour PME/ETI"}

Structure:
1. Titre accrocheur
2. Introduction (2-3 phrases)
3. Corps principal (3-4 paragraphes)
4. Call-to-action
5. Signature

Ton: Professionnel mais accessible
Longueur: 300-400 mots
"""

            response = await llm.generate(prompt, temperature=0.7, max_tokens=800)
            return response

        except Exception as e:
            logger.warning(f"[MARCEAU] LLM indisponible: {e}")
            return f"""
Chers clients,

Nous sommes heureux de vous partager nos dernieres actualites concernant {topic}.

Notre equipe travaille continuellement pour ameliorer votre experience et vous apporter les meilleurs outils de gestion.

N'hesitez pas a nous contacter pour en savoir plus.

Cordialement,
L'equipe AZALSCORE
"""

    def _format_newsletter_html(self, subject: str, content: str) -> str:
        """Formate le contenu en HTML pour l'email."""
        # Convertir les sauts de ligne en <br> et les paragraphes en <p>
        paragraphs = content.split("\n\n")
        html_paragraphs = "".join([f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs if p.strip()])

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{subject}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2563eb; }}
        p {{ margin-bottom: 15px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <h1>{subject}</h1>
    {html_paragraphs}
    <div class="footer">
        <p>Vous recevez cet email car vous etes inscrit a notre newsletter.</p>
    </div>
</body>
</html>
"""

    # =========================================================================
    # ANALYZE PERFORMANCE
    # =========================================================================

    async def _analyze_performance(self, data: dict, context: list[str]) -> dict:
        """
        Analyse les performances marketing.

        Args:
            data: {
                "period": str (week|month|quarter|year)
                "metrics": list[str] (campaigns|social|email|all)
            }

        Returns:
            Rapport de performances avec recommandations
        """
        try:
            period = data.get("period", "month")
            metrics = data.get("metrics", ["all"])

            # Calculer la periode
            now = datetime.utcnow()
            if period == "week":
                start_date = now - timedelta(days=7)
            elif period == "month":
                start_date = now - timedelta(days=30)
            elif period == "quarter":
                start_date = now - timedelta(days=90)
            else:  # year
                start_date = now - timedelta(days=365)

            stats = {}

            # Recuperer les actions marketing
            actions = self.db.query(MarceauAction).filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.module == ModuleName.MARKETING,
                MarceauAction.created_at >= start_date,
                MarceauAction.status == ActionStatus.COMPLETED,
            ).all()

            # Analyser par type d'action
            if "all" in metrics or "campaigns" in metrics:
                campaign_actions = [a for a in actions if a.action_type == "campaign_created"]
                stats["campaigns"] = {
                    "created": len(campaign_actions),
                }

            if "all" in metrics or "social" in metrics:
                social_actions = [a for a in actions if a.action_type == "social_post"]
                stats["social"] = {
                    "posts": len(social_actions),
                    "by_platform": {},
                }
                for a in social_actions:
                    platform = a.output_data.get("platform", "unknown") if a.output_data else "unknown"
                    stats["social"]["by_platform"][platform] = stats["social"]["by_platform"].get(platform, 0) + 1

            if "all" in metrics or "email" in metrics:
                email_actions = [a for a in actions if a.action_type == "newsletter_sent"]
                total_sent = sum(a.output_data.get("sent_count", 0) for a in email_actions if a.output_data)
                stats["email"] = {
                    "newsletters": len(email_actions),
                    "total_sent": total_sent,
                }

            # Generer des recommandations via LLM
            recommendations = await self._generate_recommendations(stats, context)

            # Action Marceau
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.MARKETING,
                action_type="performance_analysis",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={"stats": stats, "recommendations": recommendations},
                confidence_score=0.85,
            )
            self.db.add(action)
            self.db.commit()

            return {
                "success": True,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat(),
                "stats": stats,
                "recommendations": recommendations,
                "action_id": str(action.id),
                "module": "marketing"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur analyse performance: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "marketing"
            }

    async def _generate_recommendations(self, stats: dict, context: list[str]) -> list[str]:
        """Genere des recommandations basees sur les stats."""
        recommendations = []

        # Recommandations basiques
        if stats.get("social", {}).get("posts", 0) < 4:
            recommendations.append("Augmentez votre frequence de publication sur les reseaux sociaux (objectif: 1 post/semaine minimum)")

        if stats.get("email", {}).get("newsletters", 0) == 0:
            recommendations.append("Lancez une newsletter mensuelle pour maintenir le contact avec vos clients")

        if stats.get("campaigns", {}).get("created", 0) == 0:
            recommendations.append("Creez une campagne marketing pour promouvoir vos services")

        # Recommandation LLM si peu de contenu
        if len(recommendations) < 2:
            try:
                from app.modules.marceau.llm_client import get_llm_client_for_tenant

                llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

                prompt = f"""
Analyse ces statistiques marketing et suggere 2 recommandations concretes:

Stats: {stats}

Format: Liste a puces, maximum 2 recommandations actionables.
"""

                response = await llm.generate(prompt, temperature=0.5, max_tokens=200)

                # Extraire les recommandations
                for line in response.split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        recommendations.append(line[1:].strip())

            except Exception as e:
                logger.debug(f"[MARCEAU] Pas de recommandations LLM: {e}")

        return recommendations[:5]  # Maximum 5 recommandations

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        """Action non reconnue."""
        return {
            "success": False,
            "error": "Action non reconnue",
            "available_actions": ["create_campaign", "post_social", "send_newsletter", "analyze_performance"],
            "module": "marketing"
        }
