# Status Management System Implementation

## Overview

This document describes the implementation of a comprehensive status management system for the Prelovium application. The system allows users to manage the lifecycle of uploaded items through various statuses: `in_review`, `published`, `hidden`, `deleted`, and `sold`.

## Features Implemented

### 1. Database Schema Updates

**New Fields Added to Upload Model:**
- `status` (VARCHAR(20)): Current status of the item (default: 'in_review')
- `updated_at` (DATETIME): Timestamp of last status update

**Status Values:**
- `in_review`: Default status for new uploads
- `published`: Item is visible and available for sale
- `hidden`: Item is temporarily hidden from public view
- `deleted`: Item is marked as deleted (soft delete)
- `sold`: Item has been sold (can only be set from 'published' state)

### 2. State Transition Rules

The system enforces the following business rules:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  in_review  │────│  published  │────│    sold     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   hidden    │◄───│   deleted   │    │ (end state) │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Rules:**
- Items can only be marked as `sold` when they are in `published` state
- From any state, items can be moved to `published`, `hidden`, `deleted`, or `in_review`
- All transitions are logged with timestamps

### 3. API Endpoints

**New Endpoints:**

1. **PUT /api/uploads/<upload_id>/status**
   - Update the status of a specific item
   - Validates state transitions
   - Returns updated item data

2. **GET /api/statuses**
   - Returns all valid statuses with display names and colors
   - Used for frontend dropdown population

3. **Enhanced GET /api/uploads**
   - Added `status` query parameter for filtering
   - Example: `/api/uploads?status=published`

4. **Enhanced GET /history**
   - Added `status` query parameter for filtering
   - Example: `/history?status=in_review`

### 4. Frontend Updates

**History Page Enhancements:**

1. **Status Filtering Dropdown**
   - Filter items by status: All, In Review, Published, Hidden, Deleted, Sold
   - URL-based filtering with query parameters
   - Maintains filter state on page reload

2. **Status Badges**
   - Color-coded status indicators on each item card
   - Consistent styling across the application

3. **Action Buttons**
   - Six action buttons per item: Publish, Hide, Delete, Sell, Review
   - Context-aware button states (e.g., "Sell" only enabled for published items)
   - Real-time status updates with success/error notifications

4. **Enhanced Modal**
   - Displays current status with appropriate styling
   - Shows both created and updated timestamps
   - Better organized product information

### 5. Migration System

**Automatic Migration:**
- Database migration function that adds status columns to existing uploads
- Sets default status to 'in_review' for existing items
- Handles both SQLite and PostgreSQL databases
- Automatically runs on application startup

## Usage Examples

### 1. Filtering Items by Status

```bash
# Get only published items
curl "http://localhost:8080/api/uploads?status=published"

# Get items in review
curl "http://localhost:8080/api/uploads?status=in_review"

# Get all items
curl "http://localhost:8080/api/uploads"
```

### 2. Updating Item Status

```bash
# Publish an item
curl -X PUT "http://localhost:8080/api/uploads/item_123/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "published"}'

# Mark as sold (only works if currently published)
curl -X PUT "http://localhost:8080/api/uploads/item_123/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "sold"}'
```

### 3. Web Interface Usage

1. **Navigate to History Page:** Visit `/history`
2. **Filter by Status:** Use the dropdown to filter items
3. **Update Status:** Click action buttons on item cards
4. **View Details:** Click "View Details" for comprehensive information

## Technical Implementation Details

### Database Changes

```python
# New fields added to Upload model
status = db.Column(db.String(20), nullable=False, default='in_review')
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Valid statuses
VALID_STATUSES = ['in_review', 'published', 'hidden', 'deleted', 'sold']
```

### Status Validation

```python
def update_status(self, new_status):
    """Update status with validation."""
    if new_status not in self.VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")
    
    # Validate state transitions
    if new_status == 'sold' and self.status != 'published':
        raise ValueError("Items can only be marked as 'sold' when they are in 'published' state")
    
    self.status = new_status
    self.updated_at = datetime.utcnow()
```

### Frontend JavaScript

```javascript
// Status update with error handling
async function updateStatus(uploadId, newStatus) {
    const response = await fetch(`/api/uploads/${uploadId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error);
    }
    
    return response.json();
}
```

## Error Handling

The system includes comprehensive error handling:

1. **Invalid Status Values:** Returns 400 with descriptive error message
2. **Invalid State Transitions:** Returns 400 with transition rule explanation
3. **Non-existent Items:** Returns 404 for unknown upload IDs
4. **Database Errors:** Returns 500 with generic error message
5. **Frontend Errors:** Toast notifications for user feedback

## Security Considerations

1. **Input Validation:** All status values are validated against whitelist
2. **SQL Injection Prevention:** Using SQLAlchemy ORM with parameterized queries
3. **State Transition Validation:** Business rules enforced at database level
4. **Soft Deletes:** Items are never actually deleted from database

## Performance Considerations

1. **Database Indexing:** Status field should be indexed for efficient filtering
2. **Query Optimization:** Filtered queries use WHERE clauses to limit results
3. **Frontend Caching:** Status information cached during page load
4. **Pagination:** Consider implementing pagination for large datasets

## Testing

Run the test suite with:

```bash
python test_status_system.py
```

The test suite covers:
- Database operations and validations
- API endpoint functionality
- Status display methods
- State transition rules

## Future Enhancements

Potential improvements to consider:

1. **Audit Trail:** Log all status changes with user information
2. **Bulk Operations:** Update multiple items simultaneously
3. **Email Notifications:** Alert users of status changes
4. **Advanced Filtering:** Multiple status filters, date ranges
5. **Export Functionality:** Export filtered item lists
6. **Status Analytics:** Dashboard showing item status distribution

## Migration Guide

For existing deployments:

1. **Backup Database:** Always backup before running migrations
2. **Update Code:** Deploy new code with migration functions
3. **Run Migration:** Migration runs automatically on app startup
4. **Verify Data:** Check that existing uploads have correct default status
5. **Test Functionality:** Verify all status operations work correctly

## Troubleshooting

Common issues and solutions:

1. **Migration Fails:** Check database permissions and connection
2. **Status Not Updating:** Verify API endpoint URLs and request format
3. **Filter Not Working:** Check query parameter format and values
4. **Buttons Disabled:** Verify item is in correct state for transition
5. **UI Not Updating:** Check browser console for JavaScript errors

## Conclusion

The status management system provides a robust foundation for managing item lifecycles in the Prelovium application. It includes proper validation, error handling, and a user-friendly interface while maintaining data integrity and following business rules.

The implementation is extensible and can be enhanced with additional features as needed. The migration system ensures backward compatibility with existing data.