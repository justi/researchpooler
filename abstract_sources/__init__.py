"""Abstract source plugins for add_abstracts.py."""

from .acl_anthology import AclAnthologySource
from .pmlr import PmlrSource
from .openreview import OpenReviewSource
from .ijcai import IjcaiSource
from .isca import IscaSource
from .jmlr import JmlrSource
from .usenix import UsenixSource
from .aaai import AaaiSource
from .cvf import CvfSource
from .rss import RssSource

SOURCES = {
    "acl_anthology": AclAnthologySource,
    "pmlr": PmlrSource,
    "openreview": OpenReviewSource,
    "ijcai": IjcaiSource,
    "isca": IscaSource,
    "jmlr": JmlrSource,
    "usenix": UsenixSource,
    "aaai": AaaiSource,
    "cvf": CvfSource,
    "rss": RssSource,
}
