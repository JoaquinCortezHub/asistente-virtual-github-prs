from types import SimpleNamespace

from asistente.github_client import PullRequestService


class FakeRepo:
    def __init__(self):
        self.pull_requests = [
            SimpleNamespace(
                number=1,
                title="Abierto",
                state="open",
                merged_at=None,
                user=SimpleNamespace(login="ana"),
                html_url="https://example.test/1",
            ),
            SimpleNamespace(
                number=2,
                title="Fusionado",
                state="closed",
                merged_at="2026-01-01T00:00:00Z",
                user=SimpleNamespace(login="juan"),
                html_url="https://example.test/2",
            ),
        ]

    def get_pulls(self, **_kwargs):
        return self.pull_requests


class FakeGithub:
    def get_repo(self, _name):
        return FakeRepo()


def test_clasifica_abiertos_y_fusionados():
    service = PullRequestService("octocat/Hello-World", github=FakeGithub())
    assert [pr.number for pr in service.list_prs("abiertos")] == [1]
    assert [pr.number for pr in service.list_prs("fusionados")] == [2]
    assert service.count_prs("todos") == 2

