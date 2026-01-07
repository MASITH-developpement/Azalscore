"""
AZALS MODULE 12 - E-Commerce Service
======================================
Logique métier pour la plateforme e-commerce.
Intégration avec: Inventory, Finance, Commercial, Country Packs
"""

import uuid
import bcrypt
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc

from .models import (
    EcommerceCategory, EcommerceProduct, ProductVariant,
    EcommerceCart, CartItem, EcommerceOrder, OrderItem,
    EcommercePayment, ShippingMethod, Shipment,
    Coupon, EcommerceCustomer, CustomerAddress,
    ProductReview, Wishlist, WishlistItem,
    ProductStatus, OrderStatus, PaymentStatus, ShippingStatus,
    CartStatus, DiscountType
)
from .schemas import (
    CategoryCreate, CategoryUpdate,
    ProductCreate, ProductUpdate,
    VariantCreate, VariantUpdate,
    CartItemAdd, CheckoutRequest, OrderStatusUpdate,
    ShippingMethodCreate, ShipmentCreate,
    CouponCreate, CouponUpdate,
    CustomerRegisterRequest, CustomerAddressCreate,
    ReviewCreate, WishlistItemAdd
)


class EcommerceService:
    """Service principal e-commerce."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # CATEGORIES
    # ========================================================================

    def create_category(self, data: CategoryCreate) -> EcommerceCategory:
        """Créer une catégorie."""
        category = EcommerceCategory(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_category(self, category_id: int) -> Optional[EcommerceCategory]:
        """Récupérer une catégorie."""
        return self.db.query(EcommerceCategory).filter(
            EcommerceCategory.tenant_id == self.tenant_id,
            EcommerceCategory.id == category_id
        ).first()

    def get_categories(
        self,
        parent_id: Optional[int] = None,
        visible_only: bool = True
    ) -> List[EcommerceCategory]:
        """Lister les catégories."""
        query = self.db.query(EcommerceCategory).filter(
            EcommerceCategory.tenant_id == self.tenant_id
        )

        if parent_id is not None:
            query = query.filter(EcommerceCategory.parent_id == parent_id)

        if visible_only:
            query = query.filter(EcommerceCategory.is_visible == True)

        return query.order_by(EcommerceCategory.sort_order).all()

    def update_category(
        self,
        category_id: int,
        data: CategoryUpdate
    ) -> Optional[EcommerceCategory]:
        """Mettre à jour une catégorie."""
        category = self.get_category(category_id)
        if not category:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> bool:
        """Supprimer une catégorie."""
        category = self.get_category(category_id)
        if not category:
            return False

        self.db.delete(category)
        self.db.commit()
        return True

    # ========================================================================
    # PRODUCTS
    # ========================================================================

    def create_product(self, data: ProductCreate) -> EcommerceProduct:
        """Créer un produit."""
        product_data = data.model_dump()

        # Convertir les objets imbriqués en JSON
        if product_data.get('images'):
            product_data['images'] = [img.model_dump() if hasattr(img, 'model_dump') else img for img in product_data['images']]

        product = EcommerceProduct(
            tenant_id=self.tenant_id,
            status=ProductStatus.DRAFT,
            **product_data
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_product(self, product_id: int) -> Optional[EcommerceProduct]:
        """Récupérer un produit."""
        return self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id,
            EcommerceProduct.id == product_id
        ).first()

    def get_product_by_slug(self, slug: str) -> Optional[EcommerceProduct]:
        """Récupérer un produit par slug."""
        return self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id,
            EcommerceProduct.slug == slug
        ).first()

    def get_product_by_sku(self, sku: str) -> Optional[EcommerceProduct]:
        """Récupérer un produit par SKU."""
        return self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id,
            EcommerceProduct.sku == sku
        ).first()

    def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None,
        status: Optional[ProductStatus] = None,
        search: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock_only: bool = False,
        featured_only: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[EcommerceProduct], int]:
        """Lister les produits avec filtres et pagination."""
        query = self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id
        )

        # Filtres
        if category_id:
            query = query.filter(
                EcommerceProduct.category_ids.contains([category_id])
            )

        if status:
            query = query.filter(EcommerceProduct.status == status)

        if search:
            search_filter = or_(
                EcommerceProduct.name.ilike(f"%{search}%"),
                EcommerceProduct.sku.ilike(f"%{search}%"),
                EcommerceProduct.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        if min_price is not None:
            query = query.filter(EcommerceProduct.price >= min_price)

        if max_price is not None:
            query = query.filter(EcommerceProduct.price <= max_price)

        if in_stock_only:
            query = query.filter(EcommerceProduct.stock_quantity > 0)

        if featured_only:
            query = query.filter(EcommerceProduct.is_featured == True)

        # Total
        total = query.count()

        # Tri
        sort_column = getattr(EcommerceProduct, sort_by, EcommerceProduct.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Pagination
        offset = (page - 1) * page_size
        products = query.offset(offset).limit(page_size).all()

        return products, total

    def update_product(
        self,
        product_id: int,
        data: ProductUpdate
    ) -> Optional[EcommerceProduct]:
        """Mettre à jour un produit."""
        product = self.get_product(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Convertir les images
        if 'images' in update_data and update_data['images']:
            update_data['images'] = [
                img.model_dump() if hasattr(img, 'model_dump') else img
                for img in update_data['images']
            ]

        for field, value in update_data.items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_product(self, product_id: int) -> bool:
        """Supprimer un produit."""
        product = self.get_product(product_id)
        if not product:
            return False

        # Archiver plutôt que supprimer
        product.status = ProductStatus.ARCHIVED
        self.db.commit()
        return True

    def publish_product(self, product_id: int) -> Optional[EcommerceProduct]:
        """Publier un produit."""
        product = self.get_product(product_id)
        if not product:
            return None

        product.status = ProductStatus.ACTIVE
        product.published_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_stock(
        self,
        product_id: int,
        quantity_change: int,
        variant_id: Optional[int] = None
    ) -> bool:
        """Mettre à jour le stock."""
        if variant_id:
            variant = self.db.query(ProductVariant).filter(
                ProductVariant.tenant_id == self.tenant_id,
                ProductVariant.id == variant_id
            ).first()
            if variant:
                variant.stock_quantity += quantity_change
                self.db.commit()
                return True
        else:
            product = self.get_product(product_id)
            if product:
                product.stock_quantity += quantity_change

                # Vérifier si rupture de stock
                if product.stock_quantity <= 0:
                    product.status = ProductStatus.OUT_OF_STOCK

                self.db.commit()
                return True

        return False

    # ========================================================================
    # VARIANTS
    # ========================================================================

    def create_variant(self, data: VariantCreate) -> ProductVariant:
        """Créer une variante."""
        variant = ProductVariant(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(variant)
        self.db.commit()
        self.db.refresh(variant)
        return variant

    def get_variants(self, product_id: int) -> List[ProductVariant]:
        """Lister les variantes d'un produit."""
        return self.db.query(ProductVariant).filter(
            ProductVariant.tenant_id == self.tenant_id,
            ProductVariant.product_id == product_id
        ).order_by(ProductVariant.position).all()

    def update_variant(
        self,
        variant_id: int,
        data: VariantUpdate
    ) -> Optional[ProductVariant]:
        """Mettre à jour une variante."""
        variant = self.db.query(ProductVariant).filter(
            ProductVariant.tenant_id == self.tenant_id,
            ProductVariant.id == variant_id
        ).first()

        if not variant:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(variant, field, value)

        self.db.commit()
        self.db.refresh(variant)
        return variant

    def delete_variant(self, variant_id: int) -> bool:
        """Supprimer une variante."""
        variant = self.db.query(ProductVariant).filter(
            ProductVariant.tenant_id == self.tenant_id,
            ProductVariant.id == variant_id
        ).first()

        if not variant:
            return False

        self.db.delete(variant)
        self.db.commit()
        return True

    # ========================================================================
    # CART
    # ========================================================================

    def get_or_create_cart(
        self,
        session_id: Optional[str] = None,
        customer_id: Optional[int] = None
    ) -> EcommerceCart:
        """Récupérer ou créer un panier."""
        query = self.db.query(EcommerceCart).filter(
            EcommerceCart.tenant_id == self.tenant_id,
            EcommerceCart.status == CartStatus.ACTIVE
        )

        if customer_id:
            cart = query.filter(EcommerceCart.customer_id == customer_id).first()
        elif session_id:
            cart = query.filter(EcommerceCart.session_id == session_id).first()
        else:
            cart = None

        if not cart:
            cart = EcommerceCart(
                tenant_id=self.tenant_id,
                session_id=session_id or str(uuid.uuid4()),
                customer_id=customer_id,
                status=CartStatus.ACTIVE,
                currency="EUR",
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)

        return cart

    def get_cart(self, cart_id: int) -> Optional[EcommerceCart]:
        """Récupérer un panier."""
        return self.db.query(EcommerceCart).filter(
            EcommerceCart.tenant_id == self.tenant_id,
            EcommerceCart.id == cart_id
        ).first()

    def get_cart_items(self, cart_id: int) -> List[CartItem]:
        """Récupérer les articles du panier."""
        return self.db.query(CartItem).filter(
            CartItem.tenant_id == self.tenant_id,
            CartItem.cart_id == cart_id
        ).all()

    def add_to_cart(
        self,
        cart_id: int,
        data: CartItemAdd
    ) -> Tuple[Optional[CartItem], str]:
        """Ajouter un article au panier."""
        cart = self.get_cart(cart_id)
        if not cart:
            return None, "Panier non trouvé"

        # Récupérer le produit
        product = self.get_product(data.product_id)
        if not product:
            return None, "Produit non trouvé"

        if product.status != ProductStatus.ACTIVE:
            return None, "Produit non disponible"

        # Vérifier le stock
        if product.track_inventory and not product.allow_backorder:
            if product.stock_quantity < data.quantity:
                return None, f"Stock insuffisant (disponible: {product.stock_quantity})"

        # Déterminer le prix
        price = product.price
        if data.variant_id:
            variant = self.db.query(ProductVariant).filter(
                ProductVariant.id == data.variant_id
            ).first()
            if variant and variant.price:
                price = variant.price

        # Vérifier si l'article existe déjà
        existing_item = self.db.query(CartItem).filter(
            CartItem.cart_id == cart_id,
            CartItem.product_id == data.product_id,
            CartItem.variant_id == data.variant_id
        ).first()

        if existing_item:
            existing_item.quantity += data.quantity
            existing_item.total_price = existing_item.unit_price * existing_item.quantity
            item = existing_item
        else:
            item = CartItem(
                tenant_id=self.tenant_id,
                cart_id=cart_id,
                product_id=data.product_id,
                variant_id=data.variant_id,
                quantity=data.quantity,
                unit_price=price,
                total_price=price * data.quantity,
                custom_options=data.custom_options
            )
            self.db.add(item)

        # Flush pour que le nouvel item soit visible dans les queries
        self.db.flush()

        # Recalculer les totaux
        self._recalculate_cart_totals(cart)

        self.db.commit()
        self.db.refresh(item)
        self.db.refresh(cart)  # Rafraîchir aussi le cart
        return item, "Article ajouté"

    def update_cart_item(
        self,
        cart_id: int,
        item_id: int,
        quantity: int
    ) -> Tuple[Optional[CartItem], str]:
        """Mettre à jour la quantité d'un article."""
        item = self.db.query(CartItem).filter(
            CartItem.tenant_id == self.tenant_id,
            CartItem.cart_id == cart_id,
            CartItem.id == item_id
        ).first()

        if not item:
            return None, "Article non trouvé"

        if quantity <= 0:
            return self.remove_from_cart(cart_id, item_id)

        # Vérifier le stock
        product = self.get_product(item.product_id)
        if product and product.track_inventory and not product.allow_backorder:
            if product.stock_quantity < quantity:
                return None, f"Stock insuffisant (disponible: {product.stock_quantity})"

        item.quantity = quantity
        item.total_price = item.unit_price * quantity

        cart = self.get_cart(cart_id)
        self._recalculate_cart_totals(cart)

        self.db.commit()
        self.db.refresh(item)
        return item, "Quantité mise à jour"

    def remove_from_cart(
        self,
        cart_id: int,
        item_id: int
    ) -> Tuple[bool, str]:
        """Retirer un article du panier."""
        item = self.db.query(CartItem).filter(
            CartItem.tenant_id == self.tenant_id,
            CartItem.cart_id == cart_id,
            CartItem.id == item_id
        ).first()

        if not item:
            return False, "Article non trouvé"

        self.db.delete(item)

        cart = self.get_cart(cart_id)
        self._recalculate_cart_totals(cart)

        self.db.commit()
        return True, "Article retiré"

    def clear_cart(self, cart_id: int) -> bool:
        """Vider le panier."""
        self.db.query(CartItem).filter(
            CartItem.cart_id == cart_id
        ).delete()

        cart = self.get_cart(cart_id)
        if cart:
            cart.subtotal = Decimal('0')
            cart.discount_total = Decimal('0')
            cart.tax_total = Decimal('0')
            cart.shipping_total = Decimal('0')
            cart.total = Decimal('0')
            cart.coupon_codes = None

        self.db.commit()
        return True

    def apply_coupon(
        self,
        cart_id: int,
        coupon_code: str
    ) -> Tuple[bool, str, Optional[Decimal]]:
        """Appliquer un code promo."""
        cart = self.get_cart(cart_id)
        if not cart:
            return False, "Panier non trouvé", None

        # Vérifier le coupon
        coupon = self.db.query(Coupon).filter(
            Coupon.tenant_id == self.tenant_id,
            Coupon.code == coupon_code.upper(),
            Coupon.is_active == True
        ).first()

        if not coupon:
            return False, "Code promo invalide", None

        # Vérifier la validité
        now = datetime.utcnow()
        if coupon.starts_at and now < coupon.starts_at:
            return False, "Code promo pas encore actif", None

        if coupon.expires_at and now > coupon.expires_at:
            return False, "Code promo expiré", None

        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            return False, "Code promo épuisé", None

        if coupon.min_order_amount and cart.subtotal < coupon.min_order_amount:
            return False, f"Montant minimum requis: {coupon.min_order_amount}€", None

        # Calculer la réduction
        discount = self._calculate_coupon_discount(cart, coupon)

        # Appliquer
        existing_codes = cart.coupon_codes or []
        if coupon_code.upper() not in existing_codes:
            existing_codes.append(coupon_code.upper())
            cart.coupon_codes = existing_codes

        self._recalculate_cart_totals(cart)
        self.db.commit()

        return True, "Code promo appliqué", discount

    def remove_coupon(self, cart_id: int, coupon_code: str) -> bool:
        """Retirer un code promo."""
        cart = self.get_cart(cart_id)
        if not cart or not cart.coupon_codes:
            return False

        cart.coupon_codes = [c for c in cart.coupon_codes if c != coupon_code.upper()]
        self._recalculate_cart_totals(cart)
        self.db.commit()
        return True

    def _calculate_coupon_discount(
        self,
        cart: EcommerceCart,
        coupon: Coupon
    ) -> Decimal:
        """Calculer la réduction d'un coupon."""
        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = cart.subtotal * (coupon.discount_value / 100)
        elif coupon.discount_type == DiscountType.FIXED_AMOUNT:
            discount = coupon.discount_value
        elif coupon.discount_type == DiscountType.FREE_SHIPPING:
            discount = cart.shipping_total
        else:
            discount = Decimal('0')

        # Plafonner la réduction
        if coupon.max_discount_amount and discount > coupon.max_discount_amount:
            discount = coupon.max_discount_amount

        return discount

    def _recalculate_cart_totals(self, cart: EcommerceCart):
        """Recalculer les totaux du panier."""
        items = self.get_cart_items(cart.id)

        # Sous-total
        subtotal = sum(item.total_price for item in items)
        cart.subtotal = subtotal

        # Réductions coupons
        discount_total = Decimal('0')
        if cart.coupon_codes:
            for code in cart.coupon_codes:
                coupon = self.db.query(Coupon).filter(
                    Coupon.tenant_id == self.tenant_id,
                    Coupon.code == code
                ).first()
                if coupon:
                    discount_total += self._calculate_coupon_discount(cart, coupon)

        cart.discount_total = discount_total

        # Taxes (simplifié - 20% TVA France)
        taxable_amount = subtotal - discount_total
        cart.tax_total = taxable_amount * Decimal('0.20')

        # Total
        cart.total = subtotal - discount_total + cart.tax_total + cart.shipping_total

    # ========================================================================
    # CHECKOUT & ORDERS
    # ========================================================================

    def checkout(self, data: CheckoutRequest) -> Tuple[Optional[EcommerceOrder], str]:
        """Processus de checkout."""
        cart = self.get_cart(data.cart_id)
        if not cart:
            return None, "Panier non trouvé"

        if cart.status != CartStatus.ACTIVE:
            return None, "Panier invalide"

        items = self.get_cart_items(cart.id)
        if not items:
            return None, "Panier vide"

        # Vérifier les stocks
        for item in items:
            product = self.get_product(item.product_id)
            if product and product.track_inventory and not product.allow_backorder:
                if product.stock_quantity < item.quantity:
                    return None, f"Stock insuffisant pour {product.name}"

        # Récupérer la méthode de livraison
        shipping_method = self.db.query(ShippingMethod).filter(
            ShippingMethod.tenant_id == self.tenant_id,
            ShippingMethod.id == data.shipping_method_id
        ).first()

        if not shipping_method:
            return None, "Méthode de livraison invalide"

        # Calculer les frais de port
        shipping_total = shipping_method.price
        if shipping_method.free_shipping_threshold:
            if cart.subtotal >= shipping_method.free_shipping_threshold:
                shipping_total = Decimal('0')

        cart.shipping_total = shipping_total
        self._recalculate_cart_totals(cart)

        # Créer la commande
        order_number = self._generate_order_number()

        # Adresse de livraison (par défaut = facturation si non fournie)
        shipping = data.shipping_address or data.billing_address

        order = EcommerceOrder(
            tenant_id=self.tenant_id,
            order_number=order_number,
            cart_id=cart.id,
            channel="web",
            customer_email=data.customer_email,
            customer_phone=data.customer_phone,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            shipping_status=ShippingStatus.PENDING,
            currency=cart.currency,
            subtotal=cart.subtotal,
            discount_total=cart.discount_total,
            shipping_total=cart.shipping_total,
            tax_total=cart.tax_total,
            total=cart.total,
            coupon_codes=cart.coupon_codes,
            # Facturation
            billing_first_name=data.billing_address.first_name,
            billing_last_name=data.billing_address.last_name,
            billing_company=data.billing_address.company,
            billing_address1=data.billing_address.address1,
            billing_address2=data.billing_address.address2,
            billing_city=data.billing_address.city,
            billing_postal_code=data.billing_address.postal_code,
            billing_country=data.billing_address.country,
            billing_phone=data.billing_address.phone,
            # Livraison
            shipping_first_name=shipping.first_name,
            shipping_last_name=shipping.last_name,
            shipping_company=shipping.company,
            shipping_address1=shipping.address1,
            shipping_address2=shipping.address2,
            shipping_city=shipping.city,
            shipping_postal_code=shipping.postal_code,
            shipping_country=shipping.country,
            shipping_phone=shipping.phone,
            shipping_method=shipping_method.name,
            shipping_carrier=shipping_method.carrier,
            customer_notes=data.customer_notes
        )

        self.db.add(order)
        self.db.flush()

        # Créer les lignes de commande
        for item in items:
            product = self.get_product(item.product_id)

            order_item = OrderItem(
                tenant_id=self.tenant_id,
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                sku=product.sku if product else None,
                name=product.name if product else "Produit",
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                tax_amount=item.total_price * Decimal('0.20'),  # TVA 20%
                total=item.total_price,
                custom_options=item.custom_options
            )
            self.db.add(order_item)

            # Décrémenter le stock
            if product and product.track_inventory:
                product.stock_quantity -= item.quantity
                product.sale_count += item.quantity

        # Marquer le panier comme converti
        cart.status = CartStatus.CONVERTED
        cart.converted_to_order_id = order.id
        cart.converted_at = datetime.utcnow()

        # Incrémenter les usages des coupons
        if cart.coupon_codes:
            for code in cart.coupon_codes:
                coupon = self.db.query(Coupon).filter(
                    Coupon.tenant_id == self.tenant_id,
                    Coupon.code == code
                ).first()
                if coupon:
                    coupon.usage_count += 1

        self.db.commit()
        self.db.refresh(order)

        return order, "Commande créée"

    def _generate_order_number(self) -> str:
        """Générer un numéro de commande unique."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:6].upper()
        return f"ORD-{timestamp}-{random_part}"

    def get_order(self, order_id: int) -> Optional[EcommerceOrder]:
        """Récupérer une commande."""
        return self.db.query(EcommerceOrder).filter(
            EcommerceOrder.tenant_id == self.tenant_id,
            EcommerceOrder.id == order_id
        ).first()

    def get_order_by_number(self, order_number: str) -> Optional[EcommerceOrder]:
        """Récupérer une commande par numéro."""
        return self.db.query(EcommerceOrder).filter(
            EcommerceOrder.tenant_id == self.tenant_id,
            EcommerceOrder.order_number == order_number
        ).first()

    def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Récupérer les articles d'une commande."""
        return self.db.query(OrderItem).filter(
            OrderItem.tenant_id == self.tenant_id,
            OrderItem.order_id == order_id
        ).all()

    def list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[OrderStatus] = None,
        customer_email: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Tuple[List[EcommerceOrder], int]:
        """Lister les commandes."""
        query = self.db.query(EcommerceOrder).filter(
            EcommerceOrder.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(EcommerceOrder.status == status)

        if customer_email:
            query = query.filter(EcommerceOrder.customer_email == customer_email)

        if date_from:
            query = query.filter(EcommerceOrder.created_at >= date_from)

        if date_to:
            query = query.filter(EcommerceOrder.created_at <= date_to)

        total = query.count()

        orders = query.order_by(desc(EcommerceOrder.created_at))\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        return orders, total

    def update_order_status(
        self,
        order_id: int,
        data: OrderStatusUpdate
    ) -> Optional[EcommerceOrder]:
        """Mettre à jour le statut d'une commande."""
        order = self.get_order(order_id)
        if not order:
            return None

        if data.status:
            order.status = data.status

            # Mettre à jour les dates selon le statut
            if data.status == OrderStatus.CANCELLED:
                order.cancelled_at = datetime.utcnow()
            elif data.status == OrderStatus.REFUNDED:
                order.refunded_at = datetime.utcnow()

        if data.shipping_status:
            order.shipping_status = data.shipping_status

            if data.shipping_status == ShippingStatus.SHIPPED:
                order.shipped_at = datetime.utcnow()
            elif data.shipping_status == ShippingStatus.DELIVERED:
                order.delivered_at = datetime.utcnow()

        if data.tracking_number:
            order.tracking_number = data.tracking_number

        if data.tracking_url:
            order.tracking_url = data.tracking_url

        if data.internal_notes:
            order.internal_notes = data.internal_notes

        self.db.commit()
        self.db.refresh(order)
        return order

    def cancel_order(self, order_id: int) -> Tuple[bool, str]:
        """Annuler une commande."""
        order = self.get_order(order_id)
        if not order:
            return False, "Commande non trouvée"

        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            return False, "Impossible d'annuler une commande expédiée"

        # Restaurer le stock
        items = self.get_order_items(order_id)
        for item in items:
            if item.product_id:
                self.update_stock(item.product_id, item.quantity, item.variant_id)

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()

        self.db.commit()
        return True, "Commande annulée"

    # ========================================================================
    # PAYMENTS
    # ========================================================================

    def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        provider: str = "stripe",
        payment_method: str = "card"
    ) -> EcommercePayment:
        """Créer un paiement."""
        payment = EcommercePayment(
            tenant_id=self.tenant_id,
            order_id=order_id,
            amount=amount,
            currency="EUR",
            provider=provider,
            payment_method=payment_method,
            status=PaymentStatus.PENDING
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def confirm_payment(
        self,
        payment_id: int,
        external_id: str,
        card_brand: Optional[str] = None,
        card_last4: Optional[str] = None
    ) -> Optional[EcommercePayment]:
        """Confirmer un paiement."""
        payment = self.db.query(EcommercePayment).filter(
            EcommercePayment.tenant_id == self.tenant_id,
            EcommercePayment.id == payment_id
        ).first()

        if not payment:
            return None

        payment.status = PaymentStatus.CAPTURED
        payment.external_id = external_id
        payment.card_brand = card_brand
        payment.card_last4 = card_last4
        payment.captured_at = datetime.utcnow()

        # Mettre à jour la commande
        order = self.get_order(payment.order_id)
        if order:
            order.payment_status = PaymentStatus.CAPTURED
            order.paid_at = datetime.utcnow()
            order.status = OrderStatus.CONFIRMED

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def fail_payment(
        self,
        payment_id: int,
        error_code: str,
        error_message: str
    ) -> Optional[EcommercePayment]:
        """Marquer un paiement comme échoué."""
        payment = self.db.query(EcommercePayment).filter(
            EcommercePayment.tenant_id == self.tenant_id,
            EcommercePayment.id == payment_id
        ).first()

        if not payment:
            return None

        payment.status = PaymentStatus.FAILED
        payment.error_code = error_code
        payment.error_message = error_message
        payment.failed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payment)
        return payment

    # ========================================================================
    # SHIPPING
    # ========================================================================

    def create_shipping_method(self, data: ShippingMethodCreate) -> ShippingMethod:
        """Créer une méthode de livraison."""
        method = ShippingMethod(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(method)
        self.db.commit()
        self.db.refresh(method)
        return method

    def get_shipping_methods(
        self,
        country: Optional[str] = None,
        cart_subtotal: Optional[Decimal] = None
    ) -> List[ShippingMethod]:
        """Lister les méthodes de livraison disponibles."""
        query = self.db.query(ShippingMethod).filter(
            ShippingMethod.tenant_id == self.tenant_id,
            ShippingMethod.is_active == True
        )

        methods = query.order_by(ShippingMethod.sort_order).all()

        # Filtrer par pays si spécifié
        if country:
            methods = [m for m in methods if not m.countries or country in m.countries]

        # Filtrer par montant minimum
        if cart_subtotal:
            methods = [
                m for m in methods
                if not m.min_order_amount or cart_subtotal >= m.min_order_amount
            ]

        return methods

    def create_shipment(self, data: ShipmentCreate) -> Shipment:
        """Créer une expédition."""
        shipment_number = f"SHP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        shipment = Shipment(
            tenant_id=self.tenant_id,
            order_id=data.order_id,
            shipment_number=shipment_number,
            carrier=data.carrier,
            tracking_number=data.tracking_number,
            items=data.items,
            status=ShippingStatus.READY_TO_SHIP
        )
        self.db.add(shipment)

        # Mettre à jour le statut de la commande
        order = self.get_order(data.order_id)
        if order:
            order.shipping_status = ShippingStatus.READY_TO_SHIP
            if data.tracking_number:
                order.tracking_number = data.tracking_number

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def mark_shipment_shipped(
        self,
        shipment_id: int,
        tracking_number: Optional[str] = None
    ) -> Optional[Shipment]:
        """Marquer une expédition comme expédiée."""
        shipment = self.db.query(Shipment).filter(
            Shipment.tenant_id == self.tenant_id,
            Shipment.id == shipment_id
        ).first()

        if not shipment:
            return None

        shipment.status = ShippingStatus.SHIPPED
        shipment.shipped_at = datetime.utcnow()

        if tracking_number:
            shipment.tracking_number = tracking_number

        # Mettre à jour la commande
        order = self.get_order(shipment.order_id)
        if order:
            order.shipping_status = ShippingStatus.SHIPPED
            order.shipped_at = datetime.utcnow()
            order.status = OrderStatus.SHIPPED
            if tracking_number:
                order.tracking_number = tracking_number

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    # ========================================================================
    # COUPONS
    # ========================================================================

    def create_coupon(self, data: CouponCreate) -> Coupon:
        """Créer un coupon."""
        coupon = Coupon(
            tenant_id=self.tenant_id,
            code=data.code.upper(),
            **{k: v for k, v in data.model_dump().items() if k != 'code'}
        )
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def get_coupon(self, coupon_id: int) -> Optional[Coupon]:
        """Récupérer un coupon."""
        return self.db.query(Coupon).filter(
            Coupon.tenant_id == self.tenant_id,
            Coupon.id == coupon_id
        ).first()

    def get_coupon_by_code(self, code: str) -> Optional[Coupon]:
        """Récupérer un coupon par code."""
        return self.db.query(Coupon).filter(
            Coupon.tenant_id == self.tenant_id,
            Coupon.code == code.upper()
        ).first()

    def list_coupons(
        self,
        active_only: bool = True
    ) -> List[Coupon]:
        """Lister les coupons."""
        query = self.db.query(Coupon).filter(
            Coupon.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.filter(Coupon.is_active == True)

        return query.order_by(desc(Coupon.created_at)).all()

    def update_coupon(
        self,
        coupon_id: int,
        data: CouponUpdate
    ) -> Optional[Coupon]:
        """Mettre à jour un coupon."""
        coupon = self.get_coupon(coupon_id)
        if not coupon:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(coupon, field, value)

        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def delete_coupon(self, coupon_id: int) -> bool:
        """Désactiver un coupon."""
        coupon = self.get_coupon(coupon_id)
        if not coupon:
            return False

        coupon.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # CUSTOMERS
    # ========================================================================

    def register_customer(self, data: CustomerRegisterRequest) -> Tuple[Optional[EcommerceCustomer], str]:
        """Inscrire un client."""
        # Vérifier si l'email existe
        existing = self.db.query(EcommerceCustomer).filter(
            EcommerceCustomer.tenant_id == self.tenant_id,
            EcommerceCustomer.email == data.email
        ).first()

        if existing:
            return None, "Email déjà utilisé"

        # SECURITY FIX: Utiliser bcrypt au lieu de SHA256
        password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

        customer = EcommerceCustomer(
            tenant_id=self.tenant_id,
            email=data.email,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            accepts_marketing=data.accepts_marketing,
            marketing_opt_in_at=datetime.utcnow() if data.accepts_marketing else None
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer, "Inscription réussie"

    def get_customer(self, customer_id: int) -> Optional[EcommerceCustomer]:
        """Récupérer un client."""
        return self.db.query(EcommerceCustomer).filter(
            EcommerceCustomer.tenant_id == self.tenant_id,
            EcommerceCustomer.id == customer_id
        ).first()

    def get_customer_by_email(self, email: str) -> Optional[EcommerceCustomer]:
        """Récupérer un client par email."""
        return self.db.query(EcommerceCustomer).filter(
            EcommerceCustomer.tenant_id == self.tenant_id,
            EcommerceCustomer.email == email
        ).first()

    def authenticate_customer(
        self,
        email: str,
        password: str
    ) -> Optional[EcommerceCustomer]:
        """Authentifier un client."""
        customer = self.get_customer_by_email(email)
        if not customer or not customer.password_hash:
            return None

        # SECURITY FIX: Vérification bcrypt
        if not bcrypt.checkpw(password.encode(), customer.password_hash.encode()):
            return None

        return customer

    def add_customer_address(
        self,
        customer_id: int,
        data: CustomerAddressCreate
    ) -> CustomerAddress:
        """Ajouter une adresse client."""
        address = CustomerAddress(
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            **data.model_dump()
        )
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def get_customer_addresses(self, customer_id: int) -> List[CustomerAddress]:
        """Lister les adresses d'un client."""
        return self.db.query(CustomerAddress).filter(
            CustomerAddress.tenant_id == self.tenant_id,
            CustomerAddress.customer_id == customer_id
        ).all()

    # ========================================================================
    # REVIEWS
    # ========================================================================

    def create_review(
        self,
        data: ReviewCreate,
        customer_id: Optional[int] = None
    ) -> ProductReview:
        """Créer un avis produit."""
        review = ProductReview(
            tenant_id=self.tenant_id,
            product_id=data.product_id,
            customer_id=customer_id,
            rating=data.rating,
            title=data.title,
            content=data.content,
            author_name=data.author_name
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_product_reviews(
        self,
        product_id: int,
        approved_only: bool = True
    ) -> List[ProductReview]:
        """Lister les avis d'un produit."""
        query = self.db.query(ProductReview).filter(
            ProductReview.tenant_id == self.tenant_id,
            ProductReview.product_id == product_id
        )

        if approved_only:
            query = query.filter(ProductReview.is_approved == True)

        return query.order_by(desc(ProductReview.created_at)).all()

    def approve_review(self, review_id: int) -> bool:
        """Approuver un avis."""
        review = self.db.query(ProductReview).filter(
            ProductReview.tenant_id == self.tenant_id,
            ProductReview.id == review_id
        ).first()

        if not review:
            return False

        review.is_approved = True
        self.db.commit()
        return True

    # ========================================================================
    # WISHLIST
    # ========================================================================

    def get_or_create_wishlist(self, customer_id: int) -> Wishlist:
        """Récupérer ou créer une wishlist."""
        wishlist = self.db.query(Wishlist).filter(
            Wishlist.tenant_id == self.tenant_id,
            Wishlist.customer_id == customer_id
        ).first()

        if not wishlist:
            wishlist = Wishlist(
                tenant_id=self.tenant_id,
                customer_id=customer_id
            )
            self.db.add(wishlist)
            self.db.commit()
            self.db.refresh(wishlist)

        return wishlist

    def add_to_wishlist(
        self,
        customer_id: int,
        data: WishlistItemAdd
    ) -> WishlistItem:
        """Ajouter un article à la wishlist."""
        wishlist = self.get_or_create_wishlist(customer_id)

        # Vérifier si déjà présent
        existing = self.db.query(WishlistItem).filter(
            WishlistItem.wishlist_id == wishlist.id,
            WishlistItem.product_id == data.product_id
        ).first()

        if existing:
            return existing

        product = self.get_product(data.product_id)

        item = WishlistItem(
            tenant_id=self.tenant_id,
            wishlist_id=wishlist.id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            added_price=product.price if product else None
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_from_wishlist(self, customer_id: int, product_id: int) -> bool:
        """Retirer un article de la wishlist."""
        wishlist = self.get_or_create_wishlist(customer_id)

        item = self.db.query(WishlistItem).filter(
            WishlistItem.wishlist_id == wishlist.id,
            WishlistItem.product_id == product_id
        ).first()

        if not item:
            return False

        self.db.delete(item)
        self.db.commit()
        return True

    # ========================================================================
    # DASHBOARD & ANALYTICS
    # ========================================================================

    def get_dashboard_stats(self) -> dict:
        """Obtenir les statistiques du dashboard."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Commandes
        total_orders = self.db.query(EcommerceOrder).filter(
            EcommerceOrder.tenant_id == self.tenant_id
        ).count()

        orders_today = self.db.query(EcommerceOrder).filter(
            EcommerceOrder.tenant_id == self.tenant_id,
            EcommerceOrder.created_at >= today_start
        ).count()

        orders_this_month = self.db.query(EcommerceOrder).filter(
            EcommerceOrder.tenant_id == self.tenant_id,
            EcommerceOrder.created_at >= month_start
        ).count()

        # Revenus
        revenue_query = self.db.query(
            func.coalesce(func.sum(EcommerceOrder.total), 0)
        ).filter(
            EcommerceOrder.tenant_id == self.tenant_id,
            EcommerceOrder.payment_status == PaymentStatus.CAPTURED
        )

        total_revenue = revenue_query.scalar() or Decimal('0')

        revenue_today = self.db.query(
            func.coalesce(func.sum(EcommerceOrder.total), 0)
        ).filter(
            EcommerceOrder.tenant_id == self.tenant_id,
            EcommerceOrder.payment_status == PaymentStatus.CAPTURED,
            EcommerceOrder.created_at >= today_start
        ).scalar() or Decimal('0')

        revenue_this_month = self.db.query(
            func.coalesce(func.sum(EcommerceOrder.total), 0)
        ).filter(
            EcommerceOrder.tenant_id == self.tenant_id,
            EcommerceOrder.payment_status == PaymentStatus.CAPTURED,
            EcommerceOrder.created_at >= month_start
        ).scalar() or Decimal('0')

        # Produits
        total_products = self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id
        ).count()

        active_products = self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id,
            EcommerceProduct.status == ProductStatus.ACTIVE
        ).count()

        out_of_stock = self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id,
            EcommerceProduct.stock_quantity <= 0,
            EcommerceProduct.track_inventory == True
        ).count()

        low_stock = self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id,
            EcommerceProduct.stock_quantity > 0,
            EcommerceProduct.stock_quantity <= EcommerceProduct.low_stock_threshold,
            EcommerceProduct.track_inventory == True
        ).count()

        # Clients
        total_customers = self.db.query(EcommerceCustomer).filter(
            EcommerceCustomer.tenant_id == self.tenant_id
        ).count()

        new_customers = self.db.query(EcommerceCustomer).filter(
            EcommerceCustomer.tenant_id == self.tenant_id,
            EcommerceCustomer.created_at >= month_start
        ).count()

        # Paniers
        active_carts = self.db.query(EcommerceCart).filter(
            EcommerceCart.tenant_id == self.tenant_id,
            EcommerceCart.status == CartStatus.ACTIVE
        ).count()

        abandoned_carts = self.db.query(EcommerceCart).filter(
            EcommerceCart.tenant_id == self.tenant_id,
            EcommerceCart.status == CartStatus.ABANDONED
        ).count()

        # Calcul du taux d'abandon
        total_carts = active_carts + abandoned_carts
        abandonment_rate = (abandoned_carts / total_carts * 100) if total_carts > 0 else 0

        # Valeur moyenne commande
        avg_order_value = (total_revenue / total_orders) if total_orders > 0 else Decimal('0')

        return {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "average_order_value": float(avg_order_value),
            "revenue_today": float(revenue_today),
            "orders_today": orders_today,
            "revenue_this_month": float(revenue_this_month),
            "orders_this_month": orders_this_month,
            "total_products": total_products,
            "active_products": active_products,
            "out_of_stock_products": out_of_stock,
            "low_stock_products": low_stock,
            "total_customers": total_customers,
            "new_customers_this_month": new_customers,
            "active_carts": active_carts,
            "abandoned_carts": abandoned_carts,
            "cart_abandonment_rate": round(abandonment_rate, 2)
        }

    def get_top_selling_products(self, limit: int = 10) -> List[dict]:
        """Obtenir les produits les plus vendus."""
        products = self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id,
            EcommerceProduct.sale_count > 0
        ).order_by(desc(EcommerceProduct.sale_count)).limit(limit).all()

        return [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "sale_count": p.sale_count,
                "revenue": float(p.price * p.sale_count)
            }
            for p in products
        ]

    def get_recent_orders(self, limit: int = 10) -> List[dict]:
        """Obtenir les commandes récentes."""
        orders = self.db.query(EcommerceOrder).filter(
            EcommerceOrder.tenant_id == self.tenant_id
        ).order_by(desc(EcommerceOrder.created_at)).limit(limit).all()

        return [
            {
                "id": o.id,
                "order_number": o.order_number,
                "customer_email": o.customer_email,
                "total": float(o.total),
                "status": o.status.value,
                "created_at": o.created_at.isoformat()
            }
            for o in orders
        ]
