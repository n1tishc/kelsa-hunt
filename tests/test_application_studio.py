import unittest

from career_command_centre.application_studio import (
    ApplicationStudio,
    ScriptedStageRunner,
    VertexStageRunner,
)
from career_command_centre.role_workspace import (
    ProfileItemRevision,
    RelevantProfileContext,
    SelectedRoleSnapshot,
)


class ApplicationStudioTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = SelectedRoleSnapshot(
            id="snapshot_123",
            record_uid="role-123",
            source_url="https://example.invalid/role-123",
            captured_at=1_700_000_000,
            description="Build reliable APIs for developer workflows.",
            description_digest="description-digest",
        )
        item = ProfileItemRevision("profile_abc", "project", "Improved API reliability for internal tools.")
        self.context = RelevantProfileContext(
            id="context_123",
            snapshot_id=self.snapshot.id,
            profile_item_ids=(item.id,),
            profile_item_digests=("profile-digest",),
            selection_rationales=("Shared role terms: reliable, developer.",),
            items=(item,),
        )
        self.output = {
            "role_analyst": {
                "claims": [{
                    "id": "fit-1", "kind": "fit", "text": "Reliable API work is relevant.",
                    "evidence": [{"source": "role_snapshot", "quote": "Build reliable APIs"}],
                }],
                "draft": None,
            },
            "career_strategist": {
                "claims": [{
                    "id": "gap-1", "kind": "gap", "text": "Confirm ownership scope before applying.",
                    "evidence": [],
                }],
                "draft": None,
            },
            "application_writer": {
                "claims": [{
                    "id": "tailored-1", "kind": "tailored_material", "text": "Emphasize API reliability in the draft.",
                    "evidence": [{"source": "profile_item", "profile_item_id": "profile_abc", "quote": "Improved API reliability"}],
                }],
                "draft": "I improved API reliability for internal tools.",
            },
            "evidence_critic": {"claims": [], "draft": None},
        }

    def test_packet_keeps_four_structured_stages_and_labels_unsupported_claims(self):
        studio = ApplicationStudio(ScriptedStageRunner(self.output), now=lambda: 1_700_000_001)

        packet = studio.run(self.snapshot, self.context)

        self.assertEqual([stage.name for stage in packet.stages], [
            "role_analyst", "career_strategist", "application_writer", "evidence_critic",
        ])
        self.assertEqual(packet.stages[0].claims[0].support_state, "supported")
        self.assertEqual(packet.stages[1].claims[0].support_state, "suggestion")
        self.assertEqual(packet.stages[2].claims[0].support_state, "supported")
        self.assertEqual(len(packet.evidence_cards), 2)
        self.assertFalse(packet.reviewed)

    def test_malformed_or_unavailable_stage_is_reviewable_and_has_no_claims(self):
        malformed = dict(self.output)
        malformed["career_strategist"] = {"claims": "not a list", "draft": None}
        studio = ApplicationStudio(ScriptedStageRunner(malformed), now=lambda: 1_700_000_001)

        packet = studio.run(self.snapshot, self.context)

        stage = packet.stages[1]
        self.assertEqual(stage.status, "malformed")
        self.assertEqual(stage.claims, ())
        self.assertIn("review", stage.message.lower())

    def test_owner_edit_and_review_create_a_reviewable_packet_without_actions(self):
        studio = ApplicationStudio(ScriptedStageRunner(self.output), now=lambda: 1_700_000_001)
        packet = studio.run(self.snapshot, self.context)

        edited = studio.review(packet.id, "Owner-edited draft.")

        self.assertTrue(edited.reviewed)
        self.assertEqual(edited.owner_draft, "Owner-edited draft.")
        self.assertEqual(edited.reviewed_at, 1_700_000_001)

    def test_evidence_quote_must_belong_to_the_selected_snapshot_or_context(self):
        invalid = dict(self.output)
        invalid["role_analyst"] = {
            "claims": [{
                "id": "fit-1", "kind": "fit", "text": "Unsupported.",
                "evidence": [{"source": "role_snapshot", "quote": "invented quote"}],
            }],
            "draft": None,
        }
        studio = ApplicationStudio(ScriptedStageRunner(invalid), now=lambda: 1_700_000_001)

        packet = studio.run(self.snapshot, self.context)

        self.assertEqual(packet.stages[0].claims[0].support_state, "suggestion")
        self.assertEqual([card.claim_id for card in packet.evidence_cards], ["tailored-1"])

    def test_vertex_runner_uses_four_direct_schema_constrained_no_tools_calls(self):
        class Config:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class Types:
            GenerateContentConfig = Config

        class Models:
            def __init__(self):
                self.calls = []

            def generate_content(self, **kwargs):
                self.calls.append(kwargs)
                return type("Response", (), {"text": '{"claims":[],"draft":null}'})()

        models = Models()
        client = type("Client", (), {"models": models})()
        runner = VertexStageRunner("dedicated-project", client=(client, Types))

        output = runner.run(self.snapshot, self.context)

        self.assertEqual(list(output), ["role_analyst", "career_strategist", "application_writer", "evidence_critic"])
        self.assertEqual(len(models.calls), 4)
        self.assertTrue(all(call["config"].kwargs["response_mime_type"] == "application/json" for call in models.calls))
        self.assertTrue(all(call["config"].kwargs["max_output_tokens"] == 2_048 for call in models.calls))
        self.assertTrue(all("tools" not in call["config"].kwargs for call in models.calls))
        self.assertIn("Do not browse", models.calls[0]["contents"])

    def test_vertex_runner_stops_before_passing_malformed_output_downstream(self):
        class Config:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class Types:
            GenerateContentConfig = Config

        class Models:
            def __init__(self):
                self.calls = 0

            def generate_content(self, **kwargs):
                self.calls += 1
                return type("Response", (), {"text": '{"claims":"bad","draft":null}'})()

        models = Models()
        client = type("Client", (), {"models": models})()
        runner = VertexStageRunner("dedicated-project", client=(client, Types))

        self.assertEqual(runner.run(self.snapshot, self.context), {})
        self.assertEqual(models.calls, 1)

    def test_vertex_stage_failure_keeps_completed_stages_and_stops_dependents(self):
        class Config:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class Types:
            GenerateContentConfig = Config

        class Models:
            def __init__(self):
                self.calls = 0

            def generate_content(self, **kwargs):
                self.calls += 1
                if self.calls == 2:
                    raise RuntimeError("unavailable")
                return type("Response", (), {"text": '{"claims":[],"draft":null}'})()

        models = Models()
        client = type("Client", (), {"models": models})()
        studio = ApplicationStudio(VertexStageRunner("dedicated-project", client=(client, Types)))

        packet = studio.run(self.snapshot, self.context)

        self.assertEqual(packet.stages[0].status, "completed")
        self.assertEqual([stage.status for stage in packet.stages[1:]], ["unavailable", "unavailable", "unavailable"])
        self.assertEqual(models.calls, 2)


if __name__ == "__main__":
    unittest.main()
