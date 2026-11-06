"""Erreur métier levée par les services, convertie en réponse HTTP dans main.py."""


class ErreurMetier(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code  # 404, 409, 422...
        self.detail = detail  # message en français, clair et actionnable
        super().__init__(detail)
