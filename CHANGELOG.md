# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.0.7]

### Added
- Added new routes for feedback, similar to walks.
- Created unit tests for these new routes
- Added anonymous input for feedbacks, to ensure they remain anonymous.
    - Updated models to return None when feedback is created by anonymous user.
- Added logic to convert creator/owner IDs to full names for more human friendliness

## [0.0.6]

### Added
- Added new routes for walks:
    - "/api/v1/walks/" - root create new walk
    - "/api/v1/walks/{walk_id} - getter for specific walk
    - "/api/v1/walks/{walk_id} - putter for updating specific walk
    - "/api/v1/walks/{walk.id} - delete for specific walks.
- Updated unit testing for these new paths.

## [0.0.5]

### Added
- Added new routes "/users/me/feedback" and "/users/me/walks" which returns walk or feedback data that is owned or created by the currently logged in user. This will be utilized later, when we create the graphical front-end.
- Added unit tests for these new routes.

## [0.0.4]

### Added
- Finalized initial unit tests.

## [0.0.3]

### Added
- Updated user models to be more inline with application (roles, sites, regions, etc)
- Added more unit tests, still have more to go.

## [0.0.2]

### Added
- Corrected Mypy found errors.
- Created Pydantic settings, instead of loading using dotenv
- Implemented unit testing.

## [0.0.1]

### Added
- Added administrative user
- Added 50 random model users to replicate an actual organization
- Hooked application into PostgreSQL
- Validated APIs are protected by authentication.
- Docker runs perfectly