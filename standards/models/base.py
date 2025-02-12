from django_softdelete.models import SoftDeleteModel
from dirtyfields import DirtyFieldsMixin


class BaseModel(DirtyFieldsMixin, SoftDeleteModel):

    class Meta:
        abstract = True
