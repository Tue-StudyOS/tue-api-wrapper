from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.ilias_course_client import fetch_course_assignments
from tue_api_wrapper.ilias_learning_html import parse_exercise_assignments
from tue_api_wrapper.models import (
    IliasContentItem,
    IliasContentPage,
    IliasContentSection,
    IliasExerciseAssignment,
)


class _FakeIliasCourseClient:
    def __init__(self) -> None:
        self.assignment_targets: list[str] = []

    def fetch_content_page(self, target: str) -> IliasContentPage:
        self.content_target = target
        return IliasContentPage(
            title="Practical Machine Learning",
            page_url="https://ovidius.uni-tuebingen.de/goto.php/crs/5551408",
            sections=(
                IliasContentSection(
                    label="Weblinks",
                    items=(
                        IliasContentItem(
                            label="Slides",
                            url="https://ovidius.uni-tuebingen.de/link",
                            kind="Weblink",
                            properties=(),
                        ),
                    ),
                ),
                IliasContentSection(
                    label="Übungen",
                    items=(
                        IliasContentItem(
                            label="Assignments",
                            url="https://ovidius.uni-tuebingen.de/goto.php/exc/5653468",
                            kind="Übung",
                            properties=("Nächste Abgabefrist: 2 Tage",),
                        ),
                    ),
                ),
            ),
        )

    def fetch_exercise_assignments(self, target: str) -> tuple[IliasExerciseAssignment, ...]:
        self.assignment_targets.append(target)
        return (
            IliasExerciseAssignment(
                title="Assignment_5_submission",
                url=f"{target}?ass_id=97583",
                due_hint="In 2 Tage, 13 Stunden abzugeben",
                due_at="19. Jun 2026, 00:00",
                requirement="Verpflichtend",
                last_submission="Bisher keine Abgabe",
                submission_type="Datei",
                status="Nicht bewertet",
                team_action_url=f"{target}?cmd=submissionScreen",
            ),
        )


class IliasCourseAssignmentTests(unittest.TestCase):
    def test_fetch_course_assignments_groups_exercise_children(self) -> None:
        client = _FakeIliasCourseClient()

        page = fetch_course_assignments(client, "crs/5551408")

        self.assertEqual(client.content_target, "crs/5551408")
        self.assertEqual(client.assignment_targets, ["https://ovidius.uni-tuebingen.de/goto.php/exc/5653468"])
        self.assertEqual(page.course.title, "Practical Machine Learning")
        self.assertEqual(page.exercises[0].exercise.label, "Assignments")
        self.assertEqual(page.exercises[0].assignments[0].title, "Assignment_5_submission")

    def test_parse_practice_exam_assignment_page_shape(self) -> None:
        html = """
        <div class="il-item il-std-item">
          <div class="row">
            <div class="col-sm-3">In 2 Tage, 13 Stunden abzugeben</div>
            <div class="col-sm-9">
              <h4 class="il-item-title">
                <a href="ilias.php?cmdClass=ilAssignmentPresentationGUI&amp;ass_id=97583">Assignment_5_submission</a>
              </h4>
              <button data-action="ilias.php?cmdClass=ilExSubmissionFileGUI&amp;cmd=submissionScreen&amp;ass_id=97583">
                Datei abgeben
              </button>
              <span class="il-item-property-name">Abgabetermin</span>
              <span class="il-item-property-value">19. Jun 2026, 00:00</span>
              <span class="il-item-property-name">Anforderung</span>
              <span class="il-item-property-value">Verpflichtend</span>
              <span class="il-item-property-name">Datum der letzten Abgabe</span>
              <span class="il-item-property-value">Bisher keine Abgabe</span>
              <span class="il-item-property-name">Type</span>
              <span class="il-item-property-value">Datei</span>
              <span class="il-item-property-name">Status</span>
              <span class="il-item-property-value">Nicht bewertet</span>
            </div>
          </div>
        </div>
        """

        assignments = parse_exercise_assignments(
            html,
            "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilexercisehandlergui&ref_id=5653468",
        )

        self.assertEqual(assignments[0].title, "Assignment_5_submission")
        self.assertEqual(assignments[0].due_hint, "In 2 Tage, 13 Stunden abzugeben")
        self.assertEqual(assignments[0].due_at, "19. Jun 2026, 00:00")
        self.assertEqual(assignments[0].status, "Nicht bewertet")
        self.assertIn("submissionScreen", assignments[0].team_action_url or "")


if __name__ == "__main__":
    unittest.main()
