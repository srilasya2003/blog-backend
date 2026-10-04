import blog.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0003_alter_post_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=blog.models.post_image_upload_path,
                validators=[blog.models.validate_image_file],
            ),
        ),
    ]