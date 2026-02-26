"""
AZALS MODULE - Réseaux Sociaux - Service
========================================
"""
from __future__ import annotations


import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .models import MarketingPlatform, SocialNetworkMetrics
from .schemas import (
    GoogleAnalyticsInput, GoogleAdsInput, GoogleSearchConsoleInput,
    GoogleMyBusinessInput, MetaBusinessInput, LinkedInInput, SolocalInput,
    SocialMetricsCreate, SocialMetricsUpdate, MarketingSummary
)

logger = logging.getLogger(__name__)


class SocialNetworksService:
    """Service de gestion des métriques réseaux sociaux."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # === CRUD de base ===

    def get_metrics(
        self,
        platform: Optional[MarketingPlatform] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[SocialNetworkMetrics]:
        """Récupère les métriques avec filtres optionnels."""
        query = self.db.query(SocialNetworkMetrics).filter(
            SocialNetworkMetrics.tenant_id == self.tenant_id
        )

        if platform:
            query = query.filter(SocialNetworkMetrics.platform == platform)
        if start_date:
            query = query.filter(SocialNetworkMetrics.metrics_date >= start_date)
        if end_date:
            query = query.filter(SocialNetworkMetrics.metrics_date <= end_date)

        return query.order_by(SocialNetworkMetrics.metrics_date.desc()).limit(limit).all()

    def get_metrics_by_id(self, metrics_id: UUID) -> Optional[SocialNetworkMetrics]:
        """Récupère une entrée par ID."""
        return self.db.query(SocialNetworkMetrics).filter(
            and_(
                SocialNetworkMetrics.id == metrics_id,
                SocialNetworkMetrics.tenant_id == self.tenant_id
            )
        ).first()

    def get_or_create_metrics(
        self,
        platform: MarketingPlatform,
        metrics_date: date
    ) -> SocialNetworkMetrics:
        """Récupère ou crée une entrée pour une plateforme et une date."""
        existing = self.db.query(SocialNetworkMetrics).filter(
            and_(
                SocialNetworkMetrics.tenant_id == self.tenant_id,
                SocialNetworkMetrics.platform == platform,
                SocialNetworkMetrics.metrics_date == metrics_date
            )
        ).first()

        if existing:
            return existing

        new_metrics = SocialNetworkMetrics(
            tenant_id=self.tenant_id,
            platform=platform,
            metrics_date=metrics_date
        )
        self.db.add(new_metrics)
        self.db.commit()
        self.db.refresh(new_metrics)
        return new_metrics

    def update_metrics(
        self,
        metrics_id: UUID,
        data: SocialMetricsUpdate
    ) -> Optional[SocialNetworkMetrics]:
        """Met à jour des métriques existantes."""
        metrics = self.get_metrics_by_id(metrics_id)
        if not metrics:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(metrics, field, value)

        self.db.commit()
        self.db.refresh(metrics)
        return metrics

    def delete_metrics(self, metrics_id: UUID) -> bool:
        """Supprime une entrée."""
        metrics = self.get_metrics_by_id(metrics_id)
        if not metrics:
            return False

        self.db.delete(metrics)
        self.db.commit()
        return True

    # === Saisie simplifiée par plateforme ===

    def save_google_analytics(self, data: GoogleAnalyticsInput) -> SocialNetworkMetrics:
        """Enregistre les métriques Google Analytics."""
        metrics = self.get_or_create_metrics(
            MarketingPlatform.GOOGLE_ANALYTICS,
            data.metrics_date
        )

        metrics.sessions = data.sessions
        metrics.users = data.users
        metrics.pageviews = data.pageviews
        metrics.bounce_rate = data.bounce_rate
        metrics.avg_session_duration = data.avg_session_duration
        metrics.conversions = data.conversions
        metrics.conversion_rate = data.conversion_rate
        metrics.notes = data.notes

        self.db.commit()
        self.db.refresh(metrics)

        logger.info(f"[SOCIAL] Google Analytics mis à jour pour {data.metrics_date}")
        return metrics

    def save_google_ads(self, data: GoogleAdsInput) -> SocialNetworkMetrics:
        """Enregistre les métriques Google Ads."""
        metrics = self.get_or_create_metrics(
            MarketingPlatform.GOOGLE_ADS,
            data.metrics_date
        )

        metrics.impressions = data.impressions
        metrics.clicks = data.clicks
        metrics.cost = data.cost
        metrics.conversions = data.conversions
        metrics.ctr = data.ctr
        metrics.cpc = data.cpc
        metrics.roas = data.roas
        metrics.notes = data.notes

        self.db.commit()
        self.db.refresh(metrics)

        logger.info(f"[SOCIAL] Google Ads mis à jour pour {data.metrics_date}")
        return metrics

    def save_google_search_console(self, data: GoogleSearchConsoleInput) -> SocialNetworkMetrics:
        """Enregistre les métriques Google Search Console."""
        metrics = self.get_or_create_metrics(
            MarketingPlatform.GOOGLE_SEARCH_CONSOLE,
            data.metrics_date
        )

        metrics.impressions = data.impressions
        metrics.clicks = data.clicks
        metrics.ctr = data.ctr
        metrics.avg_position = data.avg_position
        metrics.notes = data.notes

        self.db.commit()
        self.db.refresh(metrics)

        logger.info(f"[SOCIAL] Google Search Console mis à jour pour {data.metrics_date}")
        return metrics

    def save_google_my_business(self, data: GoogleMyBusinessInput) -> SocialNetworkMetrics:
        """Enregistre les métriques Google My Business."""
        metrics = self.get_or_create_metrics(
            MarketingPlatform.GOOGLE_MY_BUSINESS,
            data.metrics_date
        )

        metrics.views = data.views
        metrics.clicks = data.clicks
        metrics.calls = data.calls
        metrics.directions = data.directions
        metrics.reviews_count = data.reviews_count
        metrics.rating = data.rating
        metrics.notes = data.notes

        self.db.commit()
        self.db.refresh(metrics)

        logger.info(f"[SOCIAL] Google My Business mis à jour pour {data.metrics_date}")
        return metrics

    def save_meta_business(self, data: MetaBusinessInput) -> SocialNetworkMetrics:
        """Enregistre les métriques Meta (Facebook ou Instagram)."""
        metrics = self.get_or_create_metrics(
            data.platform,
            data.metrics_date
        )

        metrics.reach = data.reach
        metrics.impressions = data.impressions
        metrics.engagement = data.engagement
        metrics.clicks = data.clicks
        metrics.followers = data.followers
        metrics.cost = data.cost
        metrics.ctr = data.ctr
        metrics.cpm = data.cpm
        metrics.notes = data.notes

        self.db.commit()
        self.db.refresh(metrics)

        logger.info(f"[SOCIAL] {data.platform.value} mis à jour pour {data.metrics_date}")
        return metrics

    def save_linkedin(self, data: LinkedInInput) -> SocialNetworkMetrics:
        """Enregistre les métriques LinkedIn."""
        metrics = self.get_or_create_metrics(
            MarketingPlatform.LINKEDIN,
            data.metrics_date
        )

        metrics.followers = data.followers
        metrics.impressions = data.impressions
        metrics.clicks = data.clicks
        metrics.engagement = data.engagement
        metrics.engagement_rate = data.engagement_rate
        metrics.reach = data.reach
        metrics.notes = data.notes

        self.db.commit()
        self.db.refresh(metrics)

        logger.info(f"[SOCIAL] LinkedIn mis à jour pour {data.metrics_date}")
        return metrics

    def save_solocal(self, data: SolocalInput) -> SocialNetworkMetrics:
        """Enregistre les métriques Solocal."""
        metrics = self.get_or_create_metrics(
            MarketingPlatform.SOLOCAL,
            data.metrics_date
        )

        metrics.impressions = data.impressions
        metrics.clicks = data.clicks
        metrics.calls = data.calls
        metrics.directions = data.directions
        metrics.reviews_count = data.reviews_count
        metrics.rating = data.rating
        metrics.notes = data.notes

        self.db.commit()
        self.db.refresh(metrics)

        logger.info(f"[SOCIAL] Solocal mis à jour pour {data.metrics_date}")
        return metrics

    # === Récapitulatif ===

    def get_summary(self, metrics_date: Optional[date] = None) -> MarketingSummary:
        """Génère un récapitulatif marketing pour une date donnée."""
        if not metrics_date:
            metrics_date = date.today()

        summary = MarketingSummary(date=metrics_date)

        # Récupérer toutes les métriques du jour
        metrics_list = self.db.query(SocialNetworkMetrics).filter(
            and_(
                SocialNetworkMetrics.tenant_id == self.tenant_id,
                SocialNetworkMetrics.metrics_date == metrics_date
            )
        ).all()

        total_spend = Decimal("0")
        total_conversions = 0
        total_impressions = 0
        total_clicks = 0

        for m in metrics_list:
            total_spend += m.cost or Decimal("0")
            total_conversions += m.conversions or 0
            total_impressions += m.impressions or 0
            total_clicks += m.clicks or 0

            platform_data = {
                "impressions": m.impressions,
                "clicks": m.clicks,
                "conversions": m.conversions,
                "cost": float(m.cost) if m.cost else 0,
            }

            if m.platform == MarketingPlatform.GOOGLE_ANALYTICS:
                platform_data.update({
                    "sessions": m.sessions,
                    "users": m.users,
                    "pageviews": m.pageviews,
                    "bounce_rate": float(m.bounce_rate) if m.bounce_rate else 0,
                })
                summary.google_analytics = platform_data

            elif m.platform == MarketingPlatform.GOOGLE_ADS:
                platform_data.update({
                    "ctr": float(m.ctr) if m.ctr else 0,
                    "cpc": float(m.cpc) if m.cpc else 0,
                    "roas": float(m.roas) if m.roas else 0,
                })
                summary.google_ads = platform_data

            elif m.platform == MarketingPlatform.GOOGLE_SEARCH_CONSOLE:
                platform_data.update({
                    "ctr": float(m.ctr) if m.ctr else 0,
                    "avg_position": float(m.avg_position) if m.avg_position else 0,
                })
                summary.google_search_console = platform_data

            elif m.platform == MarketingPlatform.GOOGLE_MY_BUSINESS:
                platform_data.update({
                    "views": m.views,
                    "calls": m.calls,
                    "directions": m.directions,
                    "rating": float(m.rating) if m.rating else 0,
                })
                summary.google_my_business = platform_data

            elif m.platform == MarketingPlatform.META_FACEBOOK:
                platform_data.update({
                    "reach": m.reach,
                    "engagement": m.engagement,
                    "followers": m.followers,
                })
                summary.meta_facebook = platform_data

            elif m.platform == MarketingPlatform.META_INSTAGRAM:
                platform_data.update({
                    "reach": m.reach,
                    "engagement": m.engagement,
                    "followers": m.followers,
                })
                summary.meta_instagram = platform_data

            elif m.platform == MarketingPlatform.LINKEDIN:
                platform_data.update({
                    "followers": m.followers,
                    "engagement_rate": float(m.engagement_rate) if m.engagement_rate else 0,
                })
                summary.linkedin = platform_data

            elif m.platform == MarketingPlatform.SOLOCAL:
                platform_data.update({
                    "calls": m.calls,
                    "directions": m.directions,
                    "rating": float(m.rating) if m.rating else 0,
                })
                summary.solocal = platform_data

        summary.total_spend = total_spend
        summary.total_conversions = total_conversions
        summary.total_impressions = total_impressions
        summary.total_clicks = total_clicks
        summary.overall_ctr = (
            Decimal(total_clicks) / Decimal(total_impressions) * 100
            if total_impressions > 0 else Decimal("0")
        )

        return summary

    # === Mise à jour des métriques Prometheus ===

    def sync_to_prometheus(self, metrics_date: Optional[date] = None):
        """
        Synchronise les métriques de la DB vers Prometheus.
        Appelée après chaque mise à jour ou périodiquement.
        """
        from app.core.metrics import (
            GA_SESSIONS, GA_USERS, GA_PAGEVIEWS, GA_BOUNCE_RATE,
            GA_AVG_SESSION_DURATION, GA_CONVERSIONS, GA_CONVERSION_RATE,
            GADS_IMPRESSIONS, GADS_CLICKS, GADS_COST, GADS_CONVERSIONS,
            GADS_CTR, GADS_CPC, GADS_ROAS,
            GSC_IMPRESSIONS, GSC_CLICKS, GSC_CTR, GSC_POSITION,
            META_REACH, META_IMPRESSIONS, META_ENGAGEMENT, META_CLICKS,
            META_COST, META_FOLLOWERS_FB, META_FOLLOWERS_IG, META_CTR, META_CPM,
            SOLOCAL_IMPRESSIONS, SOLOCAL_CLICKS, SOLOCAL_CALLS,
            SOLOCAL_DIRECTIONS, SOLOCAL_REVIEWS, SOLOCAL_RATING,
            LINKEDIN_FOLLOWERS, LINKEDIN_IMPRESSIONS, LINKEDIN_CLICKS,
            LINKEDIN_ENGAGEMENT_RATE, LINKEDIN_VISITORS,
            GMB_VIEWS, GMB_SEARCHES, GMB_ACTIONS, GMB_REVIEWS, GMB_RATING,
            MARKETING_TOTAL_SPEND, MARKETING_TOTAL_CONVERSIONS, MARKETING_OVERALL_ROI
        )

        if not metrics_date:
            metrics_date = date.today()

        metrics_list = self.db.query(SocialNetworkMetrics).filter(
            and_(
                SocialNetworkMetrics.tenant_id == self.tenant_id,
                SocialNetworkMetrics.metrics_date == metrics_date
            )
        ).all()

        total_spend = Decimal("0")
        total_conversions = 0

        for m in metrics_list:
            total_spend += m.cost or Decimal("0")
            total_conversions += m.conversions or 0

            if m.platform == MarketingPlatform.GOOGLE_ANALYTICS:
                GA_SESSIONS.set(m.sessions or 0)
                GA_USERS.set(m.users or 0)
                GA_PAGEVIEWS.set(m.pageviews or 0)
                GA_BOUNCE_RATE.set(float(m.bounce_rate or 0))
                GA_AVG_SESSION_DURATION.set(float(m.avg_session_duration or 0))
                GA_CONVERSIONS.set(m.conversions or 0)
                GA_CONVERSION_RATE.set(float(m.conversion_rate or 0))

            elif m.platform == MarketingPlatform.GOOGLE_ADS:
                GADS_IMPRESSIONS.set(m.impressions or 0)
                GADS_CLICKS.set(m.clicks or 0)
                GADS_COST.set(float(m.cost or 0))
                GADS_CONVERSIONS.set(m.conversions or 0)
                GADS_CTR.set(float(m.ctr or 0))
                GADS_CPC.set(float(m.cpc or 0))
                GADS_ROAS.set(float(m.roas or 0))

            elif m.platform == MarketingPlatform.GOOGLE_SEARCH_CONSOLE:
                GSC_IMPRESSIONS.set(m.impressions or 0)
                GSC_CLICKS.set(m.clicks or 0)
                GSC_CTR.set(float(m.ctr or 0))
                GSC_POSITION.set(float(m.avg_position or 0))

            elif m.platform == MarketingPlatform.GOOGLE_MY_BUSINESS:
                GMB_VIEWS.set(m.views or 0)
                GMB_SEARCHES.set(m.impressions or 0)
                GMB_ACTIONS.set((m.calls or 0) + (m.clicks or 0) + (m.directions or 0))
                GMB_REVIEWS.set(m.reviews_count or 0)
                GMB_RATING.set(float(m.rating or 0))

            elif m.platform == MarketingPlatform.META_FACEBOOK:
                META_REACH.set(m.reach or 0)
                META_IMPRESSIONS.set(m.impressions or 0)
                META_ENGAGEMENT.set(m.engagement or 0)
                META_CLICKS.set(m.clicks or 0)
                META_COST.set(float(m.cost or 0))
                META_FOLLOWERS_FB.set(m.followers or 0)
                META_CTR.set(float(m.ctr or 0))
                META_CPM.set(float(m.cpm or 0))

            elif m.platform == MarketingPlatform.META_INSTAGRAM:
                META_FOLLOWERS_IG.set(m.followers or 0)

            elif m.platform == MarketingPlatform.LINKEDIN:
                LINKEDIN_FOLLOWERS.set(m.followers or 0)
                LINKEDIN_IMPRESSIONS.set(m.impressions or 0)
                LINKEDIN_CLICKS.set(m.clicks or 0)
                LINKEDIN_ENGAGEMENT_RATE.set(float(m.engagement_rate or 0))
                LINKEDIN_VISITORS.set(m.reach or 0)

            elif m.platform == MarketingPlatform.SOLOCAL:
                SOLOCAL_IMPRESSIONS.set(m.impressions or 0)
                SOLOCAL_CLICKS.set(m.clicks or 0)
                SOLOCAL_CALLS.set(m.calls or 0)
                SOLOCAL_DIRECTIONS.set(m.directions or 0)
                SOLOCAL_REVIEWS.set(m.reviews_count or 0)
                SOLOCAL_RATING.set(float(m.rating or 0))

        MARKETING_TOTAL_SPEND.set(float(total_spend))
        MARKETING_TOTAL_CONVERSIONS.set(total_conversions)

        # Calcul ROI estimé (simplifié)
        if total_spend > 0 and total_conversions > 0:
            # Supposons une valeur moyenne de conversion de 50€
            estimated_revenue = total_conversions * 50
            roi = ((estimated_revenue - float(total_spend)) / float(total_spend)) * 100
            MARKETING_OVERALL_ROI.set(roi)

        logger.info(f"[SOCIAL] Métriques Prometheus synchronisées pour {metrics_date}")
