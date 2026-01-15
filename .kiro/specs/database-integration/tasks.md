# Implementation Plan: Database Integration

## Overview

This implementation plan integrates SQLite database into MentorMind to replace in-memory storage. The implementation uses SQLAlchemy ORM and follows a bottom-up approach: database setup → models → services → routes.

## Tasks

- [x] 1. Set up database infrastructure
  - [x] 1.1 Create database configuration module
    - Create `backend/app/database.py`
    - Configure SQLAlchemy with Flask
    - Support DATABASE_URL env var for MySQL
    - Default to SQLite at `backend/data/mentormind.db`
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 1.2 Update Flask app initialization
    - Modify `backend/app/__init__.py` to initialize database
    - Create data directory if not exists
    - Call `db.create_all()` on startup
    - _Requirements: 1.4, 6.1, 6.4_
  - [x] 1.3 Add SQLAlchemy to requirements
    - Add `flask-sqlalchemy` and `sqlalchemy` to requirements.txt
    - _Requirements: 1.3_

- [x] 2. Create database models
  - [x] 2.1 Create User model
    - Create `backend/app/models/user.py`
    - Define User table with all required fields
    - Add relationships to Session, Content, QuizResult
    - _Requirements: 2.4_
  - [x] 2.2 Create Session model
    - Create `backend/app/models/session.py`
    - Define Session table with token and expiration
    - Add `is_expired` property and `create_for_user` class method
    - _Requirements: 3.2_
  - [x] 2.3 Create Content model
    - Create `backend/app/models/content.py`
    - Define Content table with file metadata
    - Add JSON properties for key_points and topics
    - _Requirements: 4.2_
  - [x] 2.4 Create QuizResult model
    - Create `backend/app/models/quiz_result.py`
    - Define QuizResult table with score tracking
    - Add JSON property for answers
    - _Requirements: 5.2_
  - [x] 2.5 Create models __init__.py
    - Create `backend/app/models/__init__.py`
    - Export all models for easy importing
    - _Requirements: 1.3_

- [x] 3. Checkpoint - Verify database setup
  - Ensure database file is created
  - Verify all tables are created
  - Ask the user if questions arise

- [x] 4. Update AuthService for database persistence
  - [x] 4.1 Rewrite AuthService to use SQLAlchemy
    - Update `backend/app/services/auth_service.py`
    - Implement `register()` with database persistence
    - Implement `login()` with credential validation
    - Implement `create_anonymous()` for anonymous users
    - Implement `validate_token()` for session validation
    - Implement `logout()` to invalidate sessions
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 3.1, 3.3, 3.4, 3.5_
  - [x] 4.2 Write property test for user persistence round-trip
    - **Property 1: User Persistence Round-Trip**
    - **Validates: Requirements 2.1, 2.3, 2.5**
  - [x] 4.3 Write property test for authentication correctness
    - **Property 2: Authentication Correctness**
    - **Validates: Requirements 2.2**
  - [x] 4.4 Write property test for session lifecycle
    - **Property 3: Session Lifecycle Validity**
    - **Validates: Requirements 3.1, 3.3, 3.4**

- [x] 5. Update auth routes
  - [x] 5.1 Update auth routes to use new AuthService
    - Update `backend/app/routes/auth.py`
    - Update register endpoint
    - Update login endpoint
    - Update anonymous endpoint
    - Add logout endpoint
    - _Requirements: 2.1, 2.2, 2.3, 3.1_
  - [x] 5.2 Create authentication decorator
    - Create `require_auth` decorator for protected routes
    - Validate token from Authorization header
    - Return 401 for invalid/expired tokens
    - _Requirements: 3.3, 3.4_

- [x] 6. Checkpoint - Verify authentication
  - Test register, login, anonymous flows
  - Verify 401 errors are fixed
  - Ensure all tests pass
  - Ask the user if questions arise

- [x] 7. Update ContentService for database persistence
  - [x] 7.1 Rewrite ContentService to use SQLAlchemy
    - Update `backend/app/services/content_service.py`
    - Implement `save_content()` with file and DB storage
    - Implement `update_content_metadata()` for AI extraction results
    - Implement `get_user_content()` for listing
    - Implement `get_content()` for single item
    - Implement `delete_content()` for removal
    - _Requirements: 4.1, 4.3, 4.4, 4.5_
  - [x] 7.2 Write property test for content user isolation
    - **Property 4: Content User Isolation**
    - **Validates: Requirements 4.3**
  - [x] 7.3 Write property test for content persistence round-trip
    - **Property 5: Content Persistence Round-Trip**
    - **Validates: Requirements 4.1, 4.5**
  - [x] 7.4 Write property test for content deletion completeness
    - **Property 6: Content Deletion Completeness**
    - **Validates: Requirements 4.4**

- [x] 8. Update content routes
  - [x] 8.1 Update content routes to use new ContentService
    - Update `backend/app/routes/content.py`
    - Add `require_auth` decorator to all endpoints
    - Update upload endpoint to save to database
    - Update list endpoint to filter by user
    - Add delete endpoint
    - _Requirements: 4.1, 4.3, 4.4_

- [x] 9. Checkpoint - Verify content management
  - Test content upload and listing
  - Verify user isolation works
  - Ensure all tests pass
  - Ask the user if questions arise

- [x] 10. Update ProgressService for database persistence
  - [x] 10.1 Rewrite ProgressService to use SQLAlchemy
    - Update `backend/app/services/progress_service.py`
    - Implement `record_quiz_result()` for saving results
    - Implement `get_progress()` for aggregated stats
    - Calculate topic-wise progress from stored results
    - _Requirements: 5.1, 5.3, 5.4, 5.5_
  - [x] 10.2 Write property test for progress calculation accuracy
    - **Property 7: Progress Calculation Accuracy**
    - **Validates: Requirements 5.1, 5.3, 5.5**
  - [x] 10.3 Write property test for topic progress tracking
    - **Property 8: Topic Progress Tracking**
    - **Validates: Requirements 5.4**

- [x] 11. Update progress and quiz routes
  - [x] 11.1 Update progress routes
    - Update `backend/app/routes/progress.py`
    - Add `require_auth` decorator
    - Use new ProgressService for data
    - _Requirements: 5.3, 5.5_
  - [x] 11.2 Update quiz routes to record results
    - Update `backend/app/routes/quiz.py`
    - Record quiz results on submission
    - _Requirements: 5.1_

- [ ] 12. Checkpoint - Verify progress tracking
  - Test quiz submission and progress
  - Verify progress calculations
  - Ensure all tests pass
  - Ask the user if questions arise

- [ ] 13. Final integration and testing
  - [ ] 13.1 Write property test for data persistence across restarts
    - **Property 9: Data Persistence Across Restarts**
    - **Validates: Requirements 6.2**
  - [ ] 13.2 Add error handling for database operations
    - Implement try/catch for database errors
    - Return appropriate HTTP status codes
    - Log errors for debugging
    - _Requirements: 7.1, 7.2, 7.4_
  - [ ] 13.3 Update .gitignore for database files
    - Add `backend/data/*.db` to .gitignore
    - Keep data directory but ignore database files

- [ ] 14. Final checkpoint - Complete integration verification
  - Run all property-based tests
  - Test end-to-end flow
  - Verify no 401 errors on authenticated routes
  - Ask the user if questions arise

## Notes

- All tasks including property-based tests are required
- SQLite is used by default for simplicity
- Set DATABASE_URL environment variable for MySQL in production
- Database file is stored in `backend/data/mentormind.db`
- User-uploaded files are stored in `backend/uploads/{user_id}/`
