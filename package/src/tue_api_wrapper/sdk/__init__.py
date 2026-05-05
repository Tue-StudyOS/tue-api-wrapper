from .authenticated import TuebingenAuthenticatedClient
from .credentials import UniversityCredentials
from .discovery import CourseDiscoveryApi
from .portal import AuthenticatedPortalApi
from .public import TuebingenPublicClient

__all__ = [
    "AuthenticatedPortalApi",
    "CourseDiscoveryApi",
    "TuebingenAuthenticatedClient",
    "TuebingenPublicClient",
    "UniversityCredentials",
]
