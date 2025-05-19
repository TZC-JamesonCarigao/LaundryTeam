import os
import django
import json
from django.core.serializers import serialize
from django.apps import apps

# Setup Django environment (adjust the path if needed)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Application.settings')
django.setup()

def dump_model_in_batches(app_label, model_name, batch_size=10):
    Model = apps.get_model(app_label, model_name)
    total = Model.objects.count()
    print(f"Total records in {model_name}: {total}")

    failed_ids = []

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        pks = Model.objects.values_list('pk', flat=True).order_by('pk')[start:end]
        print(f"Trying records PKs {list(pks)}")

        try:
            data = serialize('json', Model.objects.filter(pk__in=pks))
            filename = f"{model_name}_batch_{start}_{end}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"Successfully dumped batch {start} to {end} in {filename}")
        except Exception as e:
            print(f"Failed to dump batch {start} to {end} - error: {e}")
            failed_ids.extend(pks)

    if failed_ids:
        print(f"Failed to dump the following record IDs: {failed_ids}")
    else:
        print("All batches dumped successfully.")

# Example usage (change app and model as needed):
if __name__ == "__main__":
    dump_model_in_batches('LaundryApplication', 'Customer', batch_size=5)
