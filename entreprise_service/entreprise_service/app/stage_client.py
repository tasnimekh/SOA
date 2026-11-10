import os
import httpx
from fastapi import HTTPException

STAGE_SERVICE_URL = os.getenv("STAGE_SERVICE_URL", "http://127.0.0.1:8000")


class StageClient:
    """Client HTTP du Stage Service (contrat d'API commun)."""

    def __init__(self, base_url: str = STAGE_SERVICE_URL):
        self.base_url = base_url.rstrip("/")

    def _appel(self, methode: str, chemin: str, **kwargs) -> httpx.Response:
        try:
            return httpx.request(methode, f"{self.base_url}{chemin}", timeout=5.0, **kwargs)
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="Stage Service indisponible")

    def get_stage(self, id_stage: int) -> dict | None:
        """Retourne le stage (dict du contrat) ou None s'il n'existe pas."""
        r = self._appel("GET", f"/stages/{id_stage}")
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Reponse inattendue du Stage Service")
        return r.json()

    def demarrer_stage(self, id_stage: int) -> dict:
        """Passe le stage au statut 'en_cours' via PUT /stages/{id}."""
        r = self._appel("PUT", f"/stages/{id_stage}", json={"statut": "en_cours"})
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Impossible de demarrer le stage")
        return r.json()


def get_stage_client() -> StageClient:
    return StageClient()
