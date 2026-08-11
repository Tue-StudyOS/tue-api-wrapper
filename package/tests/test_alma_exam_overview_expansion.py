from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.client import AlmaClient


TREE_ID = "examsReadonly:overviewAsTreeReadonly:tree:ExamOverviewForPersonTreeReadonly"


def _row(
    *,
    level: int,
    path: str,
    title: str,
    kind: str,
    number: str = "",
    grade: str = "",
    cp: str = "",
    status: str = "",
    collapsed: bool = False,
) -> str:
    button = (
        f'<button class="treeTableIcon" name="{TREE_ID}:{path}:toggle" '
        f'aria-expanded="false" type="submit" title="{title} aufklappen"></button>'
        if collapsed
        else ""
    )
    return f"""
      <tr class="treeTableCellLevel{level}">
        <td>{button}</td><td></td><td></td><td></td>
        <td colspan="2"><img class="submitImageTable" alt="{kind}" />
          <span id="node:{path}:unDeftxt">{title}</span></td>
        <td><span id="node:{path}:elementnr">{number}</span></td>
        <td><span id="node:{path}:attempt">1</span></td><td></td>
        <td><span id="node:{path}:grade">{grade}</span></td>
        <td><span id="node:{path}:bonus">{cp}</span></td>
        <td><span id="node:{path}:malus"></span></td>
        <td><span id="node:{path}:workstatus">{status}</span></td>
        <td><span id="node:{path}:freeTrial">-</span></td>
        <td><span id="node:{path}:remark"></span></td>
        <td><span id="node:{path}:exceptionNein">Nein</span></td>
        <td></td><td><span id="node:{path}:geplantesFreigabedatum"></span></td>
      </tr>
    """


def _page(tree_rows: str) -> str:
    return f"""
      <form id="examsReadonly" action="/alma/exams?_flowExecutionKey=e1s1">
        <input type="hidden" name="examsReadonly_SUBMIT" value="1" />
        <input type="hidden" name="javax.faces.ViewState" value="view-1" />
        <table class="treeTableWithIcons">{tree_rows}</table>
      </form>
    """


def _partial(tree_rows: str, view_state: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
      <partial-response><changes>
        <update id="{TREE_ID}"><![CDATA[{tree_rows}]]></update>
        <update id="j_id:javax.faces.ViewState:1"><![CDATA[{view_state}]]></update>
      </changes></partial-response>
    """


INITIAL_PAGE = _page(
    _row(
        level=3,
        path="0",
        title="Studienbegleitende Leistungen",
        kind="Konto",
        status="PV",
        collapsed=True,
    )
)
FIRST_EXPANSION = _partial(
    _row(
        level=3,
        path="0",
        title="Studienbegleitende Leistungen",
        kind="Konto",
        status="PV",
    )
    + _row(
        level=4,
        path="0:0",
        title="Studienbereich Informatik",
        kind="Modul",
        status="PV",
        collapsed=True,
    ),
    "view-2",
)
SECOND_EXPANSION = _partial(
    _row(
        level=3,
        path="0",
        title="Studienbegleitende Leistungen",
        kind="Konto",
        status="PV",
    )
    + _row(
        level=4,
        path="0:0",
        title="Studienbereich Informatik",
        kind="Modul",
        status="PV",
    )
    + _row(
        level=5,
        path="0:0:0",
        title="Practical Informatics",
        kind="Prüfung",
        number="INFO-PRAK-3-6CP",
        grade="2.3",
        cp="6.0",
        status="BE",
    )
    + _row(
        level=5,
        path="0:0:1",
        title="Computer Science",
        kind="Prüfung",
        number="INFO-INFO-6-3CP",
        grade="1.0",
        cp="3.0",
        status="BE",
    ),
    "view-3",
)


class _Response:
    def __init__(self, text: str) -> None:
        self.url = "https://alma.example/alma/exams?_flowExecutionKey=e1s1"
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _Session:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.posts: list[dict[str, str]] = []
        self._post_responses = [FIRST_EXPANSION, SECOND_EXPANSION]

    def get(self, url: str, timeout: int, allow_redirects: bool = True) -> _Response:
        return _Response(INITIAL_PAGE)

    def post(
        self,
        url: str,
        data: dict[str, str],
        timeout: int,
        allow_redirects: bool = True,
    ) -> _Response:
        self.posts.append(dict(data))
        return _Response(self._post_responses.pop(0))


class AlmaExamOverviewExpansionTests(unittest.TestCase):
    def test_fetch_exam_overview_recursively_expands_lazy_tree(self) -> None:
        session = _Session()
        client = AlmaClient(base_url="https://alma.example", session=session)

        rows = client.fetch_exam_overview()

        passed = [row for row in rows if row.status == "BE"]
        self.assertEqual([(row.number, row.cp) for row in passed], [
            ("INFO-PRAK-3-6CP", "6.0"),
            ("INFO-INFO-6-3CP", "3.0"),
        ])
        self.assertEqual(len(session.posts), 2)
        self.assertEqual(session.posts[1]["javax.faces.ViewState"], "view-2")
        self.assertEqual(session.posts[0]["javax.faces.partial.execute"], f"{TREE_ID} ")
        self.assertEqual(
            session.posts[0]["javax.faces.partial.render"],
            f"{TREE_ID} examsReadonly:messages-infobox ",
        )


if __name__ == "__main__":
    unittest.main()
