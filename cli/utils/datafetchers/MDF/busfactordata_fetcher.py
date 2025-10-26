from cli.utils.datafetchers.MDF.basemetricdata_fetcher import BaseDataFetcher
from typing import Any, Dict


class BusFactorDataFetcher(BaseDataFetcher):
    """
    Class for fetching Bus Factor-related data.
    """

    def __init__(self):
        super().__init__()

    def fetch_Modeldata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data.get("bus_factor_data", {"bus_factor": "unknown"})
