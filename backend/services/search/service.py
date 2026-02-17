from typing import List, Optional
from backend.services.search.repository import DrugRepository
from backend.services.search.utils import normalize_text
from backend.core.schemas import SearchResult
from backend.core.models import Drug

class SearchService:
    def __init__(self, repository: DrugRepository = None):
        self.repository = repository or DrugRepository()

    def search_medication(self, query: str, lang: str = "fr") -> List[SearchResult]:
        clean_query = normalize_text(query)
        if len(clean_query) < 3:
            return []

        substances = self.repository.search_substances(clean_query, lang)
        
        drugs = self.repository.search_drugs(clean_query, lang)
        
        results = substances + drugs
        
        return results[:20]

    def get_details(self, cis: str) -> Optional[Drug]:
        return self.repository.get_drug_details(cis)

search_service = SearchService()
