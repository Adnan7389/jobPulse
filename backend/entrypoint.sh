#!/bin/sh

echo "🚀 Starting Entrypoint Script..."

# Only wait if both SQL_HOST and SQL_PORT are set
if [ -n "$SQL_HOST" ] && [ -n "$SQL_PORT" ]; then
    echo "⏳ Waiting for database at $SQL_HOST:$SQL_PORT..."
    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.5
    done
    echo "✅ Database is reachable!"
else
    echo "ℹ️ Skipping database wait (SQL_HOST/SQL_PORT not set). Using DATABASE_URL."
fi

echo "📦 Running Migrations..."
python manage.py migrate --no-input || echo "⚠️ Migration failed (checking if DB is ready...)"

# Run the CMD
echo "✨ Starting Web Server..."
exec "$@"
