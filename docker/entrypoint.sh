#!/bin/bash
set -e

echo "Starting entrypoint script..."

# Start PostgreSQL
echo "Starting PostgreSQL..."
service postgresql start

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h localhost -p 5432; do
    sleep 2
done
echo "PostgreSQL is ready!"

# Set password for postgres user first
echo "Setting postgres user password..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"

# Now create database and user
echo "Setting up database..."
PGPASSWORD=postgres psql -h localhost -U postgres <<-EOSQL
    -- Create user if not exists
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER:-capstone}') THEN
            CREATE USER ${DB_USER:-capstone} WITH PASSWORD '${DB_PASSWORD:-capstone}';
        END IF;
    END
    \$\$;
    
    -- Create database if not exists
    SELECT 'CREATE DATABASE ${DB_NAME:-medisafe}' 
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME:-medisafe}')\gexec
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME:-medisafe} TO ${DB_USER:-capstone};
    
    -- Grant schema privileges
    \c ${DB_NAME:-medisafe}
    GRANT ALL ON SCHEMA public TO ${DB_USER:-capstone};
EOSQL

echo "Database setup complete!"

# Install Python dependencies using install_gpu.sh
echo "Installing Python dependencies..."
cd /app
if [ -f "install_gpu.sh" ]; then
    chmod +x install_gpu.sh
    ./install_gpu.sh
else
    echo "install_gpu.sh not found, installing requirements.txt directly..."
    pip install --no-cache-dir -r requirements.txt
fi

# Run Django migrations
echo "Running Django migrations..."
python manage.py makemigrations
python manage.py migrate

# Run initDB.py to populate tables
echo "Running initDB.py..."
if [ -f "initDB.py" ]; then
    python initDB.py
else
    echo "initDB.py not found, skipping database initialization..."
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Set proper permissions
echo "Setting permissions..."
chown -R www-data:www-data /app
chmod -R 755 /app

# Start Apache
echo "Starting Apache..."
source /etc/apache2/envvars
apache2ctl -D FOREGROUND