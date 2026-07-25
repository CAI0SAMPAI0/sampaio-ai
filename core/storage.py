from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    def _open(self, name, mode="rb"):
        from accounts.models import StoredFile

        try:
            stored = StoredFile.objects.get(name=name)
            return ContentFile(stored.content, name=name)
        except StoredFile.DoesNotExist:
            raise FileNotFoundError(f"File not found: {name}")

    def _save(self, name, content):
        from accounts.models import StoredFile

        data = content.read()
        # Ensure we use a clean path name for storage
        clean_name = name.replace("\\", "/")
        StoredFile.objects.update_or_create(
            name=clean_name, defaults={"content": data, "size": len(data)}
        )
        return clean_name

    def exists(self, name):
        from accounts.models import StoredFile

        clean_name = name.replace("\\", "/")
        return StoredFile.objects.filter(name=clean_name).exists()

    def url(self, name):
        from django.conf import settings

        media_url = settings.MEDIA_URL
        if not media_url.endswith("/"):
            media_url += "/"
        clean_name = name.replace("\\", "/").lstrip("/")
        return f"{media_url}{clean_name}"

    def size(self, name):
        from accounts.models import StoredFile

        clean_name = name.replace("\\", "/")
        try:
            return StoredFile.objects.get(name=clean_name).size
        except StoredFile.DoesNotExist:
            return 0

    def delete(self, name):
        from accounts.models import StoredFile

        clean_name = name.replace("\\", "/")
        StoredFile.objects.filter(name=clean_name).delete()
