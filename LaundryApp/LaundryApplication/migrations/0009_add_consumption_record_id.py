from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('LaundryApplication', '0008_recreate_meter_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='meterdata',
            name='consumptionRecordId',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.RunSQL(
            # Add index on consumptionRecordId
            """
            CREATE INDEX IF NOT EXISTS "LaundryApplication_meterid_consumption_id_idx" 
            ON "LaundryApplication_meterdata" ("consumptionRecordId");
            """,
            """
            DROP INDEX IF EXISTS "LaundryApplication_meterid_consumption_id_idx";
            """
        ),
    ]
