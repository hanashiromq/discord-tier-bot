# Tier Bot - Discord Bot Architecture

## Overview

This is a Discord bot designed to manage tier-based applications and assignments for gaming communities. The bot handles player registration, tier applications, and administrative functions for assigning tiers to players. It uses SQLite for data persistence and Discord.py for bot functionality.

## System Architecture

### Backend Architecture
- **Framework**: Discord.py with async/await patterns
- **Database**: PostgreSQL with asyncpg for async operations
- **Configuration**: Environment-based configuration with fallback defaults
- **Structure**: Modular design with separate concerns for database, commands, models, and views
- **Persistence**: Persistent views system for button functionality across bot restarts
- **Monitoring**: Keep-alive Flask server for continuous operation

### Key Design Decisions
- **Async-first approach**: All database operations and Discord interactions use async/await for better performance
- **Modular separation**: Clear separation between data models, database operations, bot commands, and UI components
- **Environment configuration**: Sensitive data like Discord tokens stored in environment variables
- **Tier-based hierarchy**: Five-tier system (T1-T5) with T1 being the highest tier

## Key Components

### 1. Database Layer (`database.py`)
- **Purpose**: Handles all database operations and schema management
- **Tables**: 
  - `players`: Stores player information and current tier assignments
  - `applications`: Tracks tier change requests and their status
  - `tier_assignments`: Logs all tier assignment history
- **Operations**: CRUD operations for players, applications, and tier assignments

### 2. Models (`models.py`)
- **Purpose**: Defines data structures and business logic
- **Key Classes**:
  - `Player`: Represents a registered player with tier information
  - `Application`: Represents a tier change request
  - `TierAssignment`: Represents a tier assignment action
- **Tier Hierarchy**: Defines T1-T5 ranking system

### 3. Bot Commands (`bot_commands.py`)
- **Purpose**: Implements all Discord slash commands and interactions
- **Expected Commands**:
  - Player registration and management
  - Tier application submission
  - Administrative tier assignment
  - Status checking and reporting

### 4. Views (`views.py`)
- **Purpose**: Handles Discord UI components like modals and forms
- **Key Component**: `TierApplicationModal` for collecting application data
- **Form Fields**: Game ID, nickname, clan, page info, desired tier

### 5. Configuration (`config.py`)
- **Purpose**: Centralizes all configuration settings
- **Settings**: Command prefixes, tier colors, database paths, Discord tokens
- **Tier Colors**: Visual distinction for different tiers using color codes

### 6. Main Entry Point (`main.py`)
- **Purpose**: Bot initialization and startup logic
- **Responsibilities**: Database setup, command registration, Discord connection

## Data Flow

1. **Player Registration**: User submits application via Discord modal
2. **Application Storage**: Data stored in applications table with pending status
3. **Admin Review**: Administrators review and approve/reject applications
4. **Tier Assignment**: Approved applications result in tier assignments
5. **Player Update**: Player record updated with new tier information
6. **Audit Trail**: All changes logged in tier_assignments table

## External Dependencies

- **Discord.py**: Core Discord bot framework
- **aiosqlite**: Async SQLite database operations
- **Python asyncio**: Async operation handling
- **Environment Variables**: For sensitive configuration (Discord tokens)

## Deployment Strategy

- **Environment**: Designed for Replit deployment
- **Database**: SQLite file-based storage (tier_bot.db)
- **Configuration**: Environment variable based for tokens and paths
- **Startup**: Single entry point via main.py

## Database Schema

### Players Table
- Stores player information, current tier, and assignment history
- Links Discord ID to game information
- Tracks tier assignment timestamps and administrators

### Applications Table
- Manages tier change requests
- Tracks application status and processing information
- Links to Discord message IDs for interaction management

### Tier Assignments Log
- Maintains complete audit trail of all tier changes
- Records who made changes and when
- Links to originating applications

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- July 05, 2025. System upgraded for permanent hosting and 24/7 operation
- Implemented permanent bot hosting system with automatic restart functionality
- Added comprehensive monitoring dashboard with real-time status tracking
- Created multiple hosting scripts: run_forever.py, keep_bot_alive.py, startup.sh
- Added web-based monitoring interface at localhost:8080 with system metrics
- Fixed token authentication system to work with file-based tokens
- Migrated from PostgreSQL back to SQLite for simpler deployment
- Implemented automatic log rotation and cleanup systems
- Added health checks and automatic failure recovery
- Created persistent workflow system that survives Replit restarts
- Bot now runs continuously with automatic restart on failures
- Full Russian language interface maintained
- System provides 24/7 uptime with comprehensive monitoring

## Changelog

Changelog:
- July 05, 2025. Initial setup and successful deployment