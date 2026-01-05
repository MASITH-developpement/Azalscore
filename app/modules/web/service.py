"""
AZALS MODULE T7 - Service Web Transverse
=========================================

Service métier pour la gestion des composants web.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import (
    Theme, Widget, WebDashboard as Dashboard, MenuItem, UIComponent,
    UserUIPreference, Shortcut, CustomPage,
    ThemeMode, WidgetType, WidgetSize, ComponentCategory,
    MenuType, PageType
)


class WebService:
    """Service de gestion des composants web."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # THÈMES
    # ========================================================================

    def create_theme(
        self,
        code: str,
        name: str,
        mode: ThemeMode = ThemeMode.LIGHT,
        primary_color: str = "#1976D2",
        secondary_color: str = "#424242",
        is_default: bool = False,
        created_by: Optional[int] = None,
        **kwargs
    ) -> Theme:
        """Créer un thème."""
        # Si is_default, retirer le défaut des autres
        if is_default:
            self._clear_default_theme()

        theme = Theme(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            mode=mode,
            primary_color=primary_color,
            secondary_color=secondary_color,
            is_default=is_default,
            created_by=created_by,
            **{k: v for k, v in kwargs.items() if hasattr(Theme, k)}
        )
        self.db.add(theme)
        self.db.commit()
        self.db.refresh(theme)
        return theme

    def get_theme(self, theme_id: int) -> Optional[Theme]:
        """Récupérer un thème par ID."""
        return self.db.query(Theme).filter(
            and_(
                Theme.tenant_id == self.tenant_id,
                Theme.id == theme_id
            )
        ).first()

    def get_theme_by_code(self, code: str) -> Optional[Theme]:
        """Récupérer un thème par code."""
        return self.db.query(Theme).filter(
            and_(
                Theme.tenant_id == self.tenant_id,
                Theme.code == code
            )
        ).first()

    def get_default_theme(self) -> Optional[Theme]:
        """Récupérer le thème par défaut."""
        return self.db.query(Theme).filter(
            and_(
                Theme.tenant_id == self.tenant_id,
                Theme.is_default == True
            )
        ).first()

    def list_themes(
        self,
        mode: Optional[ThemeMode] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Theme], int]:
        """Lister les thèmes."""
        query = self.db.query(Theme).filter(Theme.tenant_id == self.tenant_id)

        if mode:
            query = query.filter(Theme.mode == mode)
        if is_active is not None:
            query = query.filter(Theme.is_active == is_active)

        total = query.count()
        items = query.order_by(Theme.name).offset(skip).limit(limit).all()
        return items, total

    def update_theme(self, theme_id: int, **updates) -> Optional[Theme]:
        """Mettre à jour un thème."""
        theme = self.get_theme(theme_id)
        if not theme:
            return None

        if updates.get("is_default"):
            self._clear_default_theme()

        for key, value in updates.items():
            if hasattr(theme, key):
                setattr(theme, key, value)

        theme.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(theme)
        return theme

    def delete_theme(self, theme_id: int) -> bool:
        """Supprimer un thème."""
        theme = self.get_theme(theme_id)
        if not theme or theme.is_system or theme.is_default:
            return False

        self.db.delete(theme)
        self.db.commit()
        return True

    def _clear_default_theme(self):
        """Retirer le statut par défaut des thèmes."""
        self.db.query(Theme).filter(
            and_(
                Theme.tenant_id == self.tenant_id,
                Theme.is_default == True
            )
        ).update({"is_default": False})

    # ========================================================================
    # WIDGETS
    # ========================================================================

    def create_widget(
        self,
        code: str,
        name: str,
        widget_type: WidgetType,
        default_size: WidgetSize = WidgetSize.MEDIUM,
        data_source: Optional[str] = None,
        data_query: Optional[Dict] = None,
        display_config: Optional[Dict] = None,
        created_by: Optional[int] = None,
        **kwargs
    ) -> Widget:
        """Créer un widget."""
        widget = Widget(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            widget_type=widget_type,
            default_size=default_size,
            data_source=data_source,
            data_query=json.dumps(data_query) if data_query else None,
            display_config=json.dumps(display_config) if display_config else None,
            created_by=created_by
        )
        self.db.add(widget)
        self.db.commit()
        self.db.refresh(widget)
        return widget

    def get_widget(self, widget_id: int) -> Optional[Widget]:
        """Récupérer un widget par ID."""
        return self.db.query(Widget).filter(
            and_(
                Widget.tenant_id == self.tenant_id,
                Widget.id == widget_id
            )
        ).first()

    def list_widgets(
        self,
        widget_type: Optional[WidgetType] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Widget], int]:
        """Lister les widgets."""
        query = self.db.query(Widget).filter(Widget.tenant_id == self.tenant_id)

        if widget_type:
            query = query.filter(Widget.widget_type == widget_type)
        if is_active is not None:
            query = query.filter(Widget.is_active == is_active)

        total = query.count()
        items = query.order_by(Widget.name).offset(skip).limit(limit).all()
        return items, total

    def update_widget(self, widget_id: int, **updates) -> Optional[Widget]:
        """Mettre à jour un widget."""
        widget = self.get_widget(widget_id)
        if not widget:
            return None

        json_fields = ["data_query", "display_config", "chart_config", "visible_roles"]
        for key, value in updates.items():
            if hasattr(widget, key):
                if key in json_fields and value is not None:
                    setattr(widget, key, json.dumps(value))
                else:
                    setattr(widget, key, value)

        widget.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(widget)
        return widget

    def delete_widget(self, widget_id: int) -> bool:
        """Supprimer un widget."""
        widget = self.get_widget(widget_id)
        if not widget or widget.is_system:
            return False

        self.db.delete(widget)
        self.db.commit()
        return True

    # ========================================================================
    # DASHBOARDS
    # ========================================================================

    def create_dashboard(
        self,
        code: str,
        name: str,
        page_type: PageType = PageType.DASHBOARD,
        layout_type: str = "grid",
        columns: int = 4,
        widgets_config: Optional[List[Dict]] = None,
        is_default: bool = False,
        owner_id: Optional[int] = None,
        created_by: Optional[int] = None,
        **kwargs
    ) -> Dashboard:
        """Créer un dashboard."""
        if is_default:
            self._clear_default_dashboard()

        dashboard = Dashboard(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            page_type=page_type,
            layout_type=layout_type,
            columns=columns,
            widgets_config=json.dumps(widgets_config) if widgets_config else None,
            is_default=is_default,
            owner_id=owner_id,
            created_by=created_by
        )
        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def get_dashboard(self, dashboard_id: int) -> Optional[Dashboard]:
        """Récupérer un dashboard par ID."""
        return self.db.query(Dashboard).filter(
            and_(
                Dashboard.tenant_id == self.tenant_id,
                Dashboard.id == dashboard_id
            )
        ).first()

    def get_default_dashboard(self) -> Optional[Dashboard]:
        """Récupérer le dashboard par défaut."""
        return self.db.query(Dashboard).filter(
            and_(
                Dashboard.tenant_id == self.tenant_id,
                Dashboard.is_default == True
            )
        ).first()

    def list_dashboards(
        self,
        owner_id: Optional[int] = None,
        is_public: Optional[bool] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dashboard], int]:
        """Lister les dashboards."""
        query = self.db.query(Dashboard).filter(Dashboard.tenant_id == self.tenant_id)

        if owner_id is not None:
            query = query.filter(
                or_(Dashboard.owner_id == owner_id, Dashboard.is_public == True)
            )
        if is_public is not None:
            query = query.filter(Dashboard.is_public == is_public)
        if is_active is not None:
            query = query.filter(Dashboard.is_active == is_active)

        total = query.count()
        items = query.order_by(Dashboard.name).offset(skip).limit(limit).all()
        return items, total

    def update_dashboard(self, dashboard_id: int, **updates) -> Optional[Dashboard]:
        """Mettre à jour un dashboard."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        if updates.get("is_default"):
            self._clear_default_dashboard()

        json_fields = ["widgets_config", "default_filters", "visible_roles", "editable_roles"]
        for key, value in updates.items():
            if hasattr(dashboard, key):
                if key in json_fields and value is not None:
                    setattr(dashboard, key, json.dumps(value))
                else:
                    setattr(dashboard, key, value)

        dashboard.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def delete_dashboard(self, dashboard_id: int) -> bool:
        """Supprimer un dashboard."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard or dashboard.is_default:
            return False

        self.db.delete(dashboard)
        self.db.commit()
        return True

    def _clear_default_dashboard(self):
        """Retirer le statut par défaut des dashboards."""
        self.db.query(Dashboard).filter(
            and_(
                Dashboard.tenant_id == self.tenant_id,
                Dashboard.is_default == True
            )
        ).update({"is_default": False})

    # ========================================================================
    # MENUS
    # ========================================================================

    def create_menu_item(
        self,
        code: str,
        label: str,
        menu_type: MenuType = MenuType.MAIN,
        icon: Optional[str] = None,
        route: Optional[str] = None,
        parent_id: Optional[int] = None,
        sort_order: int = 0,
        **kwargs
    ) -> MenuItem:
        """Créer un élément de menu."""
        item = MenuItem(
            tenant_id=self.tenant_id,
            code=code,
            label=label,
            menu_type=menu_type,
            icon=icon,
            route=route,
            parent_id=parent_id,
            sort_order=sort_order,
            **{k: v for k, v in kwargs.items() if hasattr(MenuItem, k)}
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_menu_item(self, item_id: int) -> Optional[MenuItem]:
        """Récupérer un élément de menu."""
        return self.db.query(MenuItem).filter(
            and_(
                MenuItem.tenant_id == self.tenant_id,
                MenuItem.id == item_id
            )
        ).first()

    def list_menu_items(
        self,
        menu_type: MenuType = MenuType.MAIN,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = True
    ) -> List[MenuItem]:
        """Lister les éléments de menu."""
        query = self.db.query(MenuItem).filter(
            and_(
                MenuItem.tenant_id == self.tenant_id,
                MenuItem.menu_type == menu_type
            )
        )

        if parent_id is not None:
            query = query.filter(MenuItem.parent_id == parent_id)
        else:
            query = query.filter(MenuItem.parent_id == None)

        if is_active is not None:
            query = query.filter(MenuItem.is_active == is_active)

        return query.order_by(MenuItem.sort_order).all()

    def get_menu_tree(self, menu_type: MenuType = MenuType.MAIN) -> List[Dict]:
        """Récupérer l'arbre de menu complet."""
        items = self.db.query(MenuItem).filter(
            and_(
                MenuItem.tenant_id == self.tenant_id,
                MenuItem.menu_type == menu_type,
                MenuItem.is_active == True
            )
        ).order_by(MenuItem.sort_order).all()

        return self._build_menu_tree(items)

    def _build_menu_tree(self, items: List[MenuItem], parent_id: Optional[int] = None) -> List[Dict]:
        """Construire l'arbre de menu récursivement."""
        tree = []
        for item in items:
            if item.parent_id == parent_id:
                node = {
                    "id": item.id,
                    "code": item.code,
                    "label": item.label,
                    "icon": item.icon,
                    "route": item.route,
                    "is_separator": item.is_separator,
                    "children": self._build_menu_tree(items, item.id)
                }
                tree.append(node)
        return tree

    def update_menu_item(self, item_id: int, **updates) -> Optional[MenuItem]:
        """Mettre à jour un élément de menu."""
        item = self.get_menu_item(item_id)
        if not item:
            return None

        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)

        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_menu_item(self, item_id: int) -> bool:
        """Supprimer un élément de menu."""
        item = self.get_menu_item(item_id)
        if not item:
            return False

        # Supprimer les enfants aussi
        self.db.query(MenuItem).filter(
            and_(
                MenuItem.tenant_id == self.tenant_id,
                MenuItem.parent_id == item_id
            )
        ).delete()

        self.db.delete(item)
        self.db.commit()
        return True

    # ========================================================================
    # PRÉFÉRENCES UTILISATEUR
    # ========================================================================

    def get_user_preferences(self, user_id: int) -> Optional[UserUIPreference]:
        """Récupérer les préférences d'un utilisateur."""
        return self.db.query(UserUIPreference).filter(
            and_(
                UserUIPreference.tenant_id == self.tenant_id,
                UserUIPreference.user_id == user_id
            )
        ).first()

    def set_user_preferences(
        self,
        user_id: int,
        **preferences
    ) -> UserUIPreference:
        """Définir les préférences d'un utilisateur."""
        pref = self.get_user_preferences(user_id)

        if not pref:
            pref = UserUIPreference(
                tenant_id=self.tenant_id,
                user_id=user_id
            )
            self.db.add(pref)

        json_fields = ["custom_shortcuts", "favorite_widgets"]
        for key, value in preferences.items():
            if hasattr(pref, key):
                if key in json_fields and value is not None:
                    setattr(pref, key, json.dumps(value))
                else:
                    setattr(pref, key, value)

        pref.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(pref)
        return pref

    # ========================================================================
    # RACCOURCIS
    # ========================================================================

    def create_shortcut(
        self,
        code: str,
        name: str,
        key_combination: str,
        action_type: str,
        action_value: Optional[str] = None,
        context: str = "global",
        **kwargs
    ) -> Shortcut:
        """Créer un raccourci clavier."""
        shortcut = Shortcut(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            key_combination=key_combination,
            action_type=action_type,
            action_value=action_value,
            context=context
        )
        self.db.add(shortcut)
        self.db.commit()
        self.db.refresh(shortcut)
        return shortcut

    def list_shortcuts(
        self,
        context: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[Shortcut]:
        """Lister les raccourcis."""
        query = self.db.query(Shortcut).filter(Shortcut.tenant_id == self.tenant_id)

        if context:
            query = query.filter(Shortcut.context == context)
        if is_active is not None:
            query = query.filter(Shortcut.is_active == is_active)

        return query.order_by(Shortcut.name).all()

    # ========================================================================
    # PAGES PERSONNALISÉES
    # ========================================================================

    def create_custom_page(
        self,
        slug: str,
        title: str,
        content: Optional[str] = None,
        page_type: PageType = PageType.CUSTOM,
        created_by: Optional[int] = None,
        **kwargs
    ) -> CustomPage:
        """Créer une page personnalisée."""
        page = CustomPage(
            tenant_id=self.tenant_id,
            slug=slug,
            title=title,
            content=content,
            page_type=page_type,
            created_by=created_by,
            **{k: v for k, v in kwargs.items() if hasattr(CustomPage, k)}
        )
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        return page

    def get_custom_page(self, page_id: int) -> Optional[CustomPage]:
        """Récupérer une page par ID."""
        return self.db.query(CustomPage).filter(
            and_(
                CustomPage.tenant_id == self.tenant_id,
                CustomPage.id == page_id
            )
        ).first()

    def get_custom_page_by_slug(self, slug: str) -> Optional[CustomPage]:
        """Récupérer une page par slug."""
        return self.db.query(CustomPage).filter(
            and_(
                CustomPage.tenant_id == self.tenant_id,
                CustomPage.slug == slug
            )
        ).first()

    def list_custom_pages(
        self,
        page_type: Optional[PageType] = None,
        is_published: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[CustomPage], int]:
        """Lister les pages personnalisées."""
        query = self.db.query(CustomPage).filter(CustomPage.tenant_id == self.tenant_id)

        if page_type:
            query = query.filter(CustomPage.page_type == page_type)
        if is_published is not None:
            query = query.filter(CustomPage.is_published == is_published)

        total = query.count()
        items = query.order_by(CustomPage.title).offset(skip).limit(limit).all()
        return items, total

    def publish_page(self, page_id: int) -> Optional[CustomPage]:
        """Publier une page."""
        page = self.get_custom_page(page_id)
        if not page:
            return None

        page.is_published = True
        page.published_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(page)
        return page

    # ========================================================================
    # COMPOSANTS UI
    # ========================================================================

    def create_component(
        self,
        code: str,
        name: str,
        category: ComponentCategory,
        props_schema: Optional[Dict] = None,
        default_props: Optional[Dict] = None,
        template: Optional[str] = None,
        created_by: Optional[int] = None,
        **kwargs
    ) -> UIComponent:
        """Créer un composant UI."""
        component = UIComponent(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            category=category,
            props_schema=json.dumps(props_schema) if props_schema else None,
            default_props=json.dumps(default_props) if default_props else None,
            template=template,
            created_by=created_by
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        return component

    def list_components(
        self,
        category: Optional[ComponentCategory] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[UIComponent], int]:
        """Lister les composants UI."""
        query = self.db.query(UIComponent).filter(UIComponent.tenant_id == self.tenant_id)

        if category:
            query = query.filter(UIComponent.category == category)
        if is_active is not None:
            query = query.filter(UIComponent.is_active == is_active)

        total = query.count()
        items = query.order_by(UIComponent.name).offset(skip).limit(limit).all()
        return items, total

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def get_ui_config(self, user_id: int) -> Dict[str, Any]:
        """Récupérer la configuration UI complète pour un utilisateur."""
        prefs = self.get_user_preferences(user_id)
        theme = None

        if prefs and prefs.theme_id:
            theme = self.get_theme(prefs.theme_id)

        if not theme:
            theme = self.get_default_theme()

        return {
            "theme": {
                "id": theme.id if theme else None,
                "code": theme.code if theme else "default",
                "mode": theme.mode.value if theme else "LIGHT",
                "colors": {
                    "primary": theme.primary_color if theme else "#1976D2",
                    "secondary": theme.secondary_color if theme else "#424242",
                    "accent": theme.accent_color if theme else "#82B1FF",
                    "error": theme.error_color if theme else "#FF5252",
                    "success": theme.success_color if theme else "#4CAF50",
                }
            } if theme else None,
            "preferences": {
                "sidebar_collapsed": prefs.sidebar_collapsed if prefs else False,
                "table_density": prefs.table_density if prefs else "default",
                "table_page_size": prefs.table_page_size if prefs else 25,
                "language": prefs.language if prefs else "fr",
                "date_format": prefs.date_format if prefs else "DD/MM/YYYY",
                "timezone": prefs.timezone if prefs else "Europe/Paris",
            } if prefs else {},
            "menu": self.get_menu_tree(MenuType.MAIN),
            "shortcuts": [
                {"key": s.key_combination, "action": s.action_value}
                for s in self.list_shortcuts(context="global")
            ]
        }


def get_web_service(db: Session, tenant_id: str) -> WebService:
    """Factory pour créer une instance du service."""
    return WebService(db, tenant_id)
