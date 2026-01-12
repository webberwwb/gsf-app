"""
Stock management utilities for handling inventory in group deals.

This module provides thread-safe stock management using database row-level locking
to prevent race conditions during high concurrency scenarios.
"""

from models import db
from models.groupdeal import GroupDealProduct
from sqlalchemy import select
from flask import current_app


def check_and_reserve_stock(group_deal_id, items):
    """
    Check if sufficient stock is available for the given items and reserve it.
    
    This function uses row-level locking (SELECT FOR UPDATE) to ensure
    thread-safety during concurrent checkouts.
    
    Args:
        group_deal_id: ID of the group deal
        items: List of dicts with 'product_id' and 'quantity' keys
        
    Returns:
        tuple: (success: bool, error_message: str or None)
        
    Raises:
        Exception: If database operations fail
    """
    try:
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Get the group deal product with row-level lock to prevent race conditions
            # This ensures no other transaction can modify this row until we commit
            deal_product = db.session.query(GroupDealProduct).filter_by(
                group_deal_id=group_deal_id,
                product_id=product_id
            ).with_for_update().first()
            
            if not deal_product:
                return False, f'Product {product_id} not found in this group deal'
            
            # Check if stock management is enabled (null/None means unlimited stock)
            if deal_product.deal_stock_limit is not None:
                current_stock = deal_product.deal_stock_limit
                
                if current_stock < quantity:
                    return False, f'库存不足。商品当前库存: {current_stock}，需要: {quantity}'
                
                # Deduct stock
                deal_product.deal_stock_limit = current_stock - quantity
                current_app.logger.info(
                    f'Reserved stock for product {product_id}: {quantity} units. '
                    f'Remaining: {deal_product.deal_stock_limit}'
                )
        
        # Changes will be committed by the calling function
        return True, None
        
    except Exception as e:
        current_app.logger.error(f'Error checking/reserving stock: {e}', exc_info=True)
        raise


def restore_stock(group_deal_id, items):
    """
    Restore stock for the given items (e.g., when an order is cancelled or updated).
    
    This function uses row-level locking to ensure thread-safety.
    
    Args:
        group_deal_id: ID of the group deal
        items: List of dicts with 'product_id' and 'quantity' keys
        
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If database operations fail
    """
    try:
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Get the group deal product with row-level lock
            deal_product = db.session.query(GroupDealProduct).filter_by(
                group_deal_id=group_deal_id,
                product_id=product_id
            ).with_for_update().first()
            
            if deal_product and deal_product.deal_stock_limit is not None:
                # Restore stock
                deal_product.deal_stock_limit += quantity
                current_app.logger.info(
                    f'Restored stock for product {product_id}: {quantity} units. '
                    f'New stock: {deal_product.deal_stock_limit}'
                )
        
        return True
        
    except Exception as e:
        current_app.logger.error(f'Error restoring stock: {e}', exc_info=True)
        raise


def get_available_stock(group_deal_id, product_id):
    """
    Get the current available stock for a product in a group deal.
    
    Args:
        group_deal_id: ID of the group deal
        product_id: ID of the product
        
    Returns:
        int or None: Available stock count, or None if unlimited stock
    """
    try:
        deal_product = GroupDealProduct.query.filter_by(
            group_deal_id=group_deal_id,
            product_id=product_id
        ).first()
        
        if not deal_product:
            return None
        
        return deal_product.deal_stock_limit
        
    except Exception as e:
        current_app.logger.error(f'Error getting available stock: {e}', exc_info=True)
        return None


def update_stock_after_order_modification(group_deal_id, old_items, new_items):
    """
    Update stock when an order is modified.
    
    This function calculates the difference between old and new items and
    adjusts stock accordingly.
    
    Args:
        group_deal_id: ID of the group deal
        old_items: List of dicts with 'product_id' and 'quantity' keys (old order)
        new_items: List of dicts with 'product_id' and 'quantity' keys (new order)
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        # Build dictionaries for easy comparison
        old_quantities = {item['product_id']: item['quantity'] for item in old_items}
        new_quantities = {item['product_id']: item['quantity'] for item in new_items}
        
        # Get all affected products
        all_product_ids = set(old_quantities.keys()) | set(new_quantities.keys())
        
        # Calculate net changes and check stock availability
        for product_id in all_product_ids:
            old_qty = old_quantities.get(product_id, 0)
            new_qty = new_quantities.get(product_id, 0)
            net_change = new_qty - old_qty
            
            if net_change == 0:
                continue  # No change for this product
            
            # Get the group deal product with row-level lock
            deal_product = db.session.query(GroupDealProduct).filter_by(
                group_deal_id=group_deal_id,
                product_id=product_id
            ).with_for_update().first()
            
            if not deal_product:
                return False, f'Product {product_id} not found in this group deal'
            
            # Check if stock management is enabled
            if deal_product.deal_stock_limit is not None:
                if net_change > 0:
                    # Increasing quantity - check if enough stock
                    if deal_product.deal_stock_limit < net_change:
                        return False, f'库存不足。商品当前库存: {deal_product.deal_stock_limit}，需要增加: {net_change}'
                    deal_product.deal_stock_limit -= net_change
                else:
                    # Decreasing quantity - restore stock
                    deal_product.deal_stock_limit += abs(net_change)
                
                current_app.logger.info(
                    f'Updated stock for product {product_id}: net change {net_change}. '
                    f'New stock: {deal_product.deal_stock_limit}'
                )
        
        return True, None
        
    except Exception as e:
        current_app.logger.error(f'Error updating stock after order modification: {e}', exc_info=True)
        raise
