from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('LaundryApplication', '0007_auto_20250516_0034'),
    ]

    operations = [
        migrations.RunSQL(
            # SQL to create the table
            """
            CREATE TABLE "LaundryApplication_meterdata" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "meterId" varchar(100) NOT NULL,
                "timestamp" datetime NOT NULL,
                "value" real NOT NULL,
                "correctionFactor" real NOT NULL,
                "created_at" datetime NOT NULL,
                "consumptionRecordId" varchar(100)
            );
            """,
            # SQL to reverse the migration if needed
            'DROP TABLE "LaundryApplication_meterdata"'
        ),
    ]