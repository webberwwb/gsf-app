from models.base import BaseModel
from models import db
from sqlalchemy import Integer, Date, Index
from datetime import datetime, timezone, date

class ProductSalesStats(BaseModel):
    """Product sales statistics aggregated by date
    
    This table stores daily aggregated sales counts for products.
    Used for:
    - Showing sales trends in admin dashboard
    - Sorting products by popularity (热门商品)
    - Historical sales analysis by date range
    """
    __tablename__ = 'product_sales_stats'
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    sale_date = db.Column(Date, nullable=False, index=True)  # Date of sale (YYYY-MM-DD)
    
    # Aggregated counts for this product on this date
    quantity_sold = db.Column(Integer, default=0, nullable=False)  # Total quantity sold
    order_count = db.Column(Integer, default=0, nullable=False)  # Number of orders containing this product
    
    # Relationships
    product = db.relationship('Product', backref='sales_stats', lazy=True)
    
    # Composite unique index: one record per product per day
    __table_args__ = (
        Index('idx_product_date', 'product_id', 'sale_date', unique=True),
    )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'product_id': self.product_id,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'quantity_sold': self.quantity_sold,
            'order_count': self.order_count
        })
        return data

