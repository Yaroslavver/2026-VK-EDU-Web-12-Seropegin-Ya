from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE core_sidebar_cache (
                cache_key varchar(255) PRIMARY KEY,
                value text NOT NULL,
                expires timestamp with time zone NOT NULL
            );
            CREATE INDEX core_sidebar_cache_expires ON core_sidebar_cache (expires);
            """,
            'DROP TABLE core_sidebar_cache;',
        ),
    ]
