from cli.utils.datafetchers.MDF.basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class CodeQualityDataFetcher(BaseDataFetcher):
    """
    Class for fetching code quality-related data.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data.get("code_quality", {"code_quality": "unknown"})
