from extractors.base import BaseExtractor
from extractors.mal_xml import MALXMLExtractor
from extractors.trakt_json import TraktJSONExtractor
from extractors.nuvio_json import NuvioJSONExtractor
from extractors.simkl_api import SimklAPIExtractor

__all__ = [
    "BaseExtractor",
    "MALXMLExtractor",
    "TraktJSONExtractor",
    "NuvioJSONExtractor",
    "SimklAPIExtractor",
]
