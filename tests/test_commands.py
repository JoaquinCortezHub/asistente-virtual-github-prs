from types import SimpleNamespace

from asistente.commands import CommandProcessor


class FakeService:
    repository_name = "octocat/Hello-World"

    def __init__(self):
        self.calls = []

    def list_prs(self, status="abiertos", author=None, limit=20):
        self.calls.append(("list", status, author, limit))
        return [
            SimpleNamespace(
                number=12,
                title="Agregar documentación",
                author="octocat",
                url="https://github.com/octocat/Hello-World/pull/12",
            )
        ]

    def count_prs(self, status="abiertos", author=None):
        self.calls.append(("count", status, author))
        return 3

    def get_pr(self, number):
        return SimpleNamespace(
            number=number,
            title="Cambio probado",
            state="closed",
            merged_at=None,
            user=SimpleNamespace(login="octocat"),
            head=SimpleNamespace(ref="feature"),
            base=SimpleNamespace(ref="main"),
            body="Descripción",
            html_url="https://github.com/octocat/Hello-World/pull/12",
        )

    def reviews(self, number):
        return [SimpleNamespace(user=SimpleNamespace(login="reviewer"), state="APPROVED", body="Bien")]


def test_lista_prs_filtra_por_autor():
    service = FakeService()
    result = CommandProcessor(service).handle("listar PRs abiertos por @octocat")
    assert "#12" in result.text
    assert service.calls == [("list", "abiertos", "octocat", 20)]


def test_cuenta_prs_fusionados():
    service = FakeService()
    result = CommandProcessor(service).handle("¿cuántos PRs fusionados hay?")
    assert result.text == "Hay 3 PRs fusionados en octocat/Hello-World."
    assert service.calls == [("count", "fusionados", None)]


def test_detalle_y_revisiones():
    service = FakeService()
    detail = CommandProcessor(service).handle("detalle del PR #12")
    reviews = CommandProcessor(service).handle("revisiones del PR #12")
    assert "Cambio probado" in detail.text
    assert "reviewer" in reviews.text


def test_salir():
    result = CommandProcessor(FakeService()).handle("adiós")
    assert result.should_exit is True

