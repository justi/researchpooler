"""Abstract source plugins for add_abstracts.py."""

from .acl_anthology import AclAnthologySource
from .pmlr import PmlrSource
from .openreview import OpenReviewSource
from .ijcai import IjcaiSource
from .isca import IscaSource
from .jmlr import JmlrSource
from .usenix import UsenixSource

SOURCES = {
    "acl_anthology": AclAnthologySource,
    "pmlr": PmlrSource,
    "openreview": OpenReviewSource,
    "ijcai": IjcaiSource,
    "isca": IscaSource,
    "jmlr": JmlrSource,
    "usenix": UsenixSource,
}
