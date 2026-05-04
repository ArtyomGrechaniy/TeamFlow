from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="is_statistics_public",
            field=models.BooleanField(
                default=False,
                help_text="Allow other users to view profile statistics.",
                verbose_name="Public statistics",
            ),
        ),
    ]
