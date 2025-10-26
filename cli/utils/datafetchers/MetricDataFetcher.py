from typing import Any, Dict
from cli.utils.MetadataFetcher import MetadataFetcher
from cli.utils.datafetchers.MDF.licensedata_fetcher import LicenseDataFetcher
from cli.utils.datafetchers.MDF.busfactordata_fetcher import BusFactorDataFetcher
from cli.utils.datafetchers.MDF.datasetdata_fetcher import DatasetDataFetcher
from cli.utils.datafetchers.MDF.codequalitydata_fetcher import CodeQualityDataFetcher
from cli.utils.datafetchers.MDF.sizedata_fetcher import SizeDataFetcher
from cli.utils.datafetchers.MDF.performanceClaimsdata_fetcher import PerformanceClaimsDataFetcher
from cli.utils.datafetchers.MDF.rampuptimedata_fetcher import RampUpTimeDataFetcher
from cli.utils.datafetchers.MDF.datasetnCodedata_fetcher import DatasetAndCodeDataFetcher


class MetricDataFetcher:
    def __init__(self):
        self.MetaDataFetcher = MetadataFetcher()
        # All fetchers implementing the three methods
        self.fetchers = [
            LicenseDataFetcher(),
            BusFactorDataFetcher(),
            DatasetDataFetcher(),
            CodeQualityDataFetcher(),
            SizeDataFetcher(),
            PerformanceClaimsDataFetcher(),
            RampUpTimeDataFetcher(),
            DatasetAndCodeDataFetcher()
        ]

    def fetch_Modeldata(self, url: str) -> Dict[str, Any]:
        data = self.MetaDataFetcher.fetch(url)
        modeldata = {}
        for fetcher in self.fetchers:
            modeldata.update(fetcher.fetch_Modeldata(data))
        return modeldata

    def fetch_CodeData(self, url: str) -> Dict[str, Any]:
        data = self.MetaDataFetcher.fetch(url)
        codedata = {}
        for fetcher in self.fetchers:
            codedata.update(fetcher.fetch_Codedata(data))
        return codedata

    def fetch_DatasetData(self, url: str) -> Dict[str, Any]:
        data = self.MetaDataFetcher.fetch(url)
        datasetdata = {}
        for fetcher in self.fetchers:
            datasetdata.update(fetcher.fetch_Datasetdata(data))
        return datasetdata


if __name__ == "__main__":
    # Example URL — Hugging Face Gemma 3 model
    test_url = "https://huggingface.co/google/gemma-3-12b-it"

    print("🔍 Fetching model metadata and metrics...")
    fetcher = MetricDataFetcher()

    try:
        model_data = fetcher.fetch_Modeldata(test_url)
        print("\n✅ Model data fetched successfully!\n")
        for key, value in model_data.items():
            print(f"{key}: {value}")
        print("\nTotal fields fetched:", len(model_data))
    except Exception as e:
        print(f"\n❌ Error fetching model data: {e}")

