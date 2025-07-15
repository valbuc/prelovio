# Item Status Management System

## Overview

The Prelovium application now includes a comprehensive item status management system in the history tab that allows users to manage their uploaded items through different lifecycle states.

## Features Implemented

### ✅ Item Status States

The system supports five distinct status states for items:

1. **`in_review`** - Default state for newly uploaded items
2. **`published`** - Items that are live and available for sale
3. **`hidden`** - Items that are temporarily hidden from view
4. **`deleted`** - Items that are marked as deleted (soft delete)
5. **`sold`** - Items that have been sold

### ✅ Status Management Rules

**Business Logic:**
- New items are automatically set to `in_review` status
- Items can only be marked as `sold` when they are in `published` state
- From any state, items can be moved to: `published`, `hidden`, `deleted`, or `in_review`
- Items are never physically deleted from the database (soft delete)

**State Transitions:**
```
in_review → published, hidden, deleted, in_review
published → hidden, deleted, sold, in_review
hidden → published, deleted, in_review
deleted → published, hidden, in_review
sold → published, hidden, deleted, in_review
```

### ✅ History Tab Features

**Status Filter:**
- Dropdown filter to view items by status
- Options: All Items, In Review, Published, Hidden, Deleted, Sold
- URL-based filtering with query parameters

**Action Buttons:**
- **Publish** - Move item to published state
- **Hide** - Move item to hidden state  
- **Delete** - Move item to deleted state (soft delete)
- **Sell** - Move item to sold state (only available for published items)
- **Review** - Move item back to in_review state

**Visual Indicators:**
- Status badges with color coding:
  - `in_review` - Yellow
  - `published` - Green
  - `hidden` - Gray
  - `deleted` - Red
  - `sold` - Blue

### ✅ Database Implementation

**Database Schema:**
- `status` field added to `uploads` table with default value `in_review`
- `updated_at` timestamp field for tracking status changes
- Migration system to add status field to existing uploads

**Database Methods:**
- `update_status()` - Updates item status with validation
- `get_status_display()` - Returns human-readable status name
- `get_status_color()` - Returns color class for status styling

### ✅ API Endpoints

**Status Management:**
- `PUT /api/uploads/<upload_id>/status` - Update item status
- `GET /history?status=<status>` - Filter history by status
- `GET /api/uploads?status=<status>` - API endpoint with status filtering

**Response Format:**
```json
{
  "message": "Status updated successfully",
  "upload": {
    "upload_id": "...",
    "status": "published",
    "updated_at": "2025-07-15T06:47:22.906660"
  }
}
```

### ✅ Frontend Implementation

**JavaScript Features:**
- Async status updates with loading states
- Error handling and user notifications
- Button state management (e.g., sell button disabled for non-published items)
- Real-time UI updates after status changes

**User Experience:**
- Confirmation notifications for successful status changes
- Error messages for invalid transitions
- Automatic page refresh after status updates
- Visual feedback during API calls

## Technical Implementation

### Database Model
```python
class Upload(db.Model):
    status = db.Column(db.String(20), nullable=False, default='in_review')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    VALID_STATUSES = ['in_review', 'published', 'hidden', 'deleted', 'sold']
    
    def update_status(self, new_status):
        """Update status with validation"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        
        if new_status == 'sold' and self.status != 'published':
            raise ValueError("Items can only be marked as 'sold' when they are in 'published' state")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
        return True
```

### API Validation
- Status validation against `VALID_STATUSES`
- Business rule enforcement (sold only from published)
- Proper error handling and user feedback

### Frontend Integration
- Status filter dropdown with URL parameter support
- Action buttons with proper state management
- Modal dialogs for item details with status display
- Real-time status updates via AJAX calls

## Usage

1. **Upload Items**: New items automatically get `in_review` status
2. **Filter Items**: Use the status dropdown to filter by specific states
3. **Manage Status**: Click action buttons to change item status
4. **Track Changes**: View status history and timestamps
5. **Sell Items**: Only published items can be marked as sold

## Security & Validation

- Server-side validation for all status transitions
- Proper error handling for invalid state changes
- SQL injection protection through SQLAlchemy ORM
- Input sanitization and validation

## Testing

The system includes comprehensive validation:
- Status transition rules are enforced
- Default status assignment works correctly
- Database constraints prevent invalid states
- API endpoints handle errors gracefully

## Migration

Existing uploads are automatically migrated to include the status field with default value `in_review`.