"""PostgreSQL Migration Guide

Complete guide for migrating from MySQL to Supabase PostgreSQL.

This includes all changes made and any manual steps needed.
"""

# Migration: MySQL → Supabase PostgreSQL

## Changes Summary

### 1. Dependencies Updated

**Removed:**
- `pymysql` - MySQL Python driver

**Added:**
- `psycopg2-binary` - PostgreSQL Python driver
- `flask_migrate` - Database migrations support

**Updated requirements.txt:**
```bash
pip install psycopg2-binary
pip install flask_migrate
```

### 2. Configuration Changes

**Old (config.py):**
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@localhost/hotel_db'
```

**New (config.py):**
```python
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://localhost/hotel_db'
```

**Added connection pooling:**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

### 3. Environment Variables

**Old (.env):**
```
DATABASE_URL=mysql+pymysql://db_user:db_password@localhost/hotel_db
```

**New (.env):**
```
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
SECRET_KEY=your-secret-key
FLASK_ENV=development
```

### 4. Database Connection String Format

**MySQL (old):**
```
mysql+pymysql://user:password@localhost:3306/database
```

**PostgreSQL/Supabase (new):**
```
postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
```

**Parameters:**
- `postgres` = default Supabase user
- `password` = your Supabase project password
- `db.xxxxx.supabase.co` = your Supabase host (find in Project Settings)
- `5432` = PostgreSQL default port
- `postgres` = default database name

### 5. SQLAlchemy Models

No changes needed to model definitions! PostgreSQL and MySQL use compatible SQL.
All relationships, foreign keys, and constraints work the same.

**Note:** PostgreSQL is stricter about constraints:
- Foreign keys are enforced by default
- Unique constraints are enforced
- Check constraints are enforced

### 6. Data Migration (if you have existing MySQL data)

If you need to migrate existing data from MySQL to Supabase:

```bash
# Export from MySQL
mysqldump -u user -p database > backup.sql

# Convert to PostgreSQL (uses pgloader)
# Or manually import using PostgreSQL tools

# Import to Supabase
psql postgresql://... < converted_backup.sql
```

### 7. New Features in PostgreSQL

**Connection Pooling:**
- Automatically handles connection reuse
- Configurable pool size and recycling
- Better performance on high-traffic apps

**Advanced Queries:**
- Full-text search with `@@ ` operator
- JSON/JSONB support
- Array types
- UUID type
- Range types

### 8. Error Handling Changes

**PostgreSQL specific errors (now handled):**

```python
# Connection errors
sqlalchemy.exc.OperationalError

# Integrity errors (foreign key, unique constraint)
sqlalchemy.exc.IntegrityError

# Program errors (syntax, type mismatches)
sqlalchemy.exc.ProgrammingError
```

### 9. Files Updated for PostgreSQL

1. `requirements.txt` - Replaced pymysql with psycopg2-binary
2. `config.py` - Updated to use postgresql:// URI and connection pooling
3. `.env.example` - Updated with Supabase connection string format
4. `run.py` - Added database initialization with error handling
5. `app/__init__.py` - Updated for PostgreSQL
6. `app/models.py` - Module docstring updated (no code changes needed)
7. `app/routes/main.py` - Documentation updated
8. `app/routes/admin.py` - Documentation updated
9. `README.md` - Complete rewrite for Supabase setup
10. `app/services/excel_utils.py` - Documentation updated

### 10. New Files Added

1. `setup.py` - Database initialization script
2. `DEPLOYMENT.md` - Complete deployment guide
3. `MIGRATION.md` - This file

---

## Step-by-Step Migration Process

### For New Installation (Recommended)

1. **Create Supabase account:**
   - Sign up at supabase.com
   - Create new project
   - Note project URL and password

2. **Update .env:**
   ```bash
   copy .env.example .env
   # Edit with your Supabase credentials
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run setup script:**
   ```bash
   python setup.py
   # This creates tables and admin user
   ```

5. **Start app:**
   ```bash
   python run.py
   # Should connect successfully to Supabase
   ```

### For Existing MySQL Installation

1. **Backup your MySQL data** (if needed)
2. **Update requirements.txt** - remove pymysql, add psycopg2-binary
3. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Update .env** with Supabase credentials
5. **Run setup script:**
   ```bash
   python setup.py
   ```
6. **Migrate data** (if you have existing data)

---

## PostgreSQL-Specific Considerations

### 1. Case Sensitivity

**PostgreSQL:** Table/column names are case-insensitive (lowercased)
**MySQL:** Depends on OS

✓ Our models already work with this!

### 2. Boolean Fields

**PostgreSQL:** Uses native BOOLEAN type
**MySQL:** Uses TINYINT(1)

✓ SQLAlchemy handles conversion automatically

### 3. Auto-increment

**PostgreSQL:** Uses SERIAL or IDENTITY
**MySQL:** Uses AUTO_INCREMENT

✓ SQLAlchemy handles this automatically with `db.Integer` + `primary_key=True`

### 4. Date/Time Handling

**PostgreSQL:** Better handling of timezones
**MySQL:** Limited timezone support

✓ Our models use `datetime.utcnow` which works with both

### 5. JSON Support

**PostgreSQL:** Native JSON and JSONB types
**MySQL:** JSON type (but less efficient)

For future: You can use `db.JSON` column type for advanced features!

### 6. Transactions

**PostgreSQL:** Strong ACID compliance
**MySQL:** Depends on storage engine (InnoDB vs MyISAM)

✓ Our app uses SQLAlchemy transactions which work the same

---

## Supabase-Specific Features

### Row Level Security (RLS)

Supabase supports PostgreSQL Row Level Security:

```sql
-- Example: Only users can see their own bookings
ALTER TABLE booking ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own bookings"
ON booking
FOR SELECT
USING (auth.uid() = user_id);
```

Note: Our current app doesn't use RLS, but can be added later!

### Supabase Realtime

Real-time database updates:

```python
# Can be added later for live bookings, notifications, etc.
```

### Storage

Supabase includes object storage for images:

```python
# Can replace local file uploads with Supabase Storage
```

---

## Performance Comparison

| Feature | MySQL | PostgreSQL |
|---------|-------|------------|
| Connection pooling | Manual | Built-in |
| JSON support | Limited | Excellent |
| Full-text search | Basic | Advanced |
| UUID | Manual | Native |
| Array types | No | Yes |
| Constraints | Limited | Comprehensive |
| Transactions | InnoDB only | All tables |
| Speed (local) | Fast | Fast |
| Speed (cloud) | N/A | Supabase optimized |

---

## Rollback Plan

If you need to go back to MySQL:

1. Keep old MySQL database running
2. Update .env with MySQL connection string:
   ```
   DATABASE_URL=mysql+pymysql://user:pass@localhost/hotel_db
   ```
3. Install pymysql:
   ```bash
   pip install pymysql
   ```
4. Restart app

All code is compatible with both!

---

## Support

**PostgreSQL Questions:**
- Official docs: https://www.postgresql.org/docs/

**Supabase Questions:**
- Dashboard: https://supabase.com
- Docs: https://supabase.com/docs
- Support: https://supabase.com/support

**Flask-SQLAlchemy:**
- Docs: https://flask-sqlalchemy.palletsprojects.com/

