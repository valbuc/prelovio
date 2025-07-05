from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Upload(db.Model):
    """Model for storing information about uploaded images and their processing results."""
    
    __tablename__ = 'uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.String(100), unique=True, nullable=False)
    
    # Original image URLs in GCS
    original_primary_url = db.Column(db.String(500), nullable=False)
    original_secondary_url = db.Column(db.String(500), nullable=False)
    original_label_url = db.Column(db.String(500), nullable=False)
    
    # Processed image URLs in GCS
    processed_primary_url = db.Column(db.String(500), nullable=False)
    processed_secondary_url = db.Column(db.String(500), nullable=False)
    processed_label_url = db.Column(db.String(500), nullable=False)
    
    # AI-generated metadata
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    brand_domain = db.Column(db.String(200), nullable=True)
    size = db.Column(db.String(20), nullable=False)
    colors = db.Column(db.Text, nullable=False)  # JSON string
    materials = db.Column(db.Text, nullable=False)  # JSON string
    categories = db.Column(db.Text, nullable=False)  # JSON string
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Upload {self.upload_id}>'
    
    def to_dict(self):
        """Convert the upload record to a dictionary."""
        return {
            'id': self.id,
            'upload_id': self.upload_id,
            'original_primary_url': self.original_primary_url,
            'original_secondary_url': self.original_secondary_url,
            'original_label_url': self.original_label_url,
            'processed_primary_url': self.processed_primary_url,
            'processed_secondary_url': self.processed_secondary_url,
            'processed_label_url': self.processed_label_url,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'brand': self.brand,
            'brand_domain': self.brand_domain,
            'size': self.size,
            'colors': json.loads(self.colors),
            'materials': json.loads(self.materials),
            'categories': json.loads(self.categories),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_metadata(cls, upload_id, original_urls, processed_urls, metadata):
        """Create an Upload instance from metadata."""
        return cls(
            upload_id=upload_id,
            original_primary_url=original_urls['primary'],
            original_secondary_url=original_urls['secondary'],
            original_label_url=original_urls['label'],
            processed_primary_url=processed_urls['primary'],
            processed_secondary_url=processed_urls['secondary'],
            processed_label_url=processed_urls['label'],
            title=metadata['title'],
            description=metadata['description'],
            price=metadata['price'],
            brand=metadata['brand'],
            brand_domain=metadata.get('brand_domain', 'NA'),
            size=metadata['size'],
            colors=json.dumps(metadata['colors']),
            materials=json.dumps(metadata['materials']),
            categories=json.dumps(metadata['categories'])
        )