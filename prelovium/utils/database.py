from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


def migrate_existing_uploads():
    """Migration function to add status field to existing uploads without it."""
    try:
        # Check if we need to add the status column
        from sqlalchemy import text
        
        # Check if status column exists
        result = db.session.execute(text("PRAGMA table_info(uploads)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'status' not in columns:
            # Add status column
            db.session.execute(text("ALTER TABLE uploads ADD COLUMN status VARCHAR(20) DEFAULT 'in_review'"))
            db.session.execute(text("ALTER TABLE uploads ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            db.session.commit()
            print("Added status and updated_at columns to uploads table")
        
        # Update existing uploads without status
        uploads_without_status = db.session.execute(text("SELECT id FROM uploads WHERE status IS NULL")).fetchall()
        
        if uploads_without_status:
            db.session.execute(text("UPDATE uploads SET status = 'in_review' WHERE status IS NULL"))
            db.session.execute(text("UPDATE uploads SET updated_at = created_at WHERE updated_at IS NULL"))
            db.session.commit()
            print(f"Updated {len(uploads_without_status)} uploads with default status")
        
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        db.session.rollback()
        return False


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
    
    # Status field for item management
    status = db.Column(db.String(20), nullable=False, default='in_review')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Valid statuses
    VALID_STATUSES = ['in_review', 'published', 'hidden', 'deleted', 'sold']

    def __init__(self, **kwargs):
        """Initialize Upload with default status if not provided."""
        if 'status' not in kwargs:
            kwargs['status'] = 'in_review'
        super().__init__(**kwargs)
    
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
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
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
            categories=json.dumps(metadata['categories']),
            status='in_review'  # Default status for new items
        )
    
    def update_status(self, new_status):
        """Update the status of the upload with validation."""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {self.VALID_STATUSES}")
        
        # Validate state transitions
        if new_status == 'sold' and self.status != 'published':
            raise ValueError("Items can only be marked as 'sold' when they are in 'published' state")
        
        # All other transitions are allowed
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        return True
    
    def get_status_display(self):
        """Get a human-readable display name for the status."""
        status_display = {
            'in_review': 'In Review',
            'published': 'Published',
            'hidden': 'Hidden',
            'deleted': 'Deleted',
            'sold': 'Sold'
        }
        return status_display.get(self.status, self.status.title())
    
    def get_status_color(self):
        """Get a color class for the status display."""
        status_colors = {
            'in_review': 'yellow',
            'published': 'green',
            'hidden': 'gray',
            'deleted': 'red',
            'sold': 'blue'
        }
        return status_colors.get(self.status, 'gray')