"""Tests for the translator/renderer additions to the output pipeline enums."""

from pathlib import Path

import pcleaner.output_structures as ost


def test_new_steps_exist_and_output_remains_last():
    assert hasattr(ost.Step, "translator")
    assert hasattr(ost.Step, "renderer")
    # output must remain the logical last step for the export logic to hold.
    assert max(ost.Step) == ost.Step.output
    assert ost.Step.inpainter < ost.Step.translator < ost.Step.renderer < ost.Step.output


def test_new_outputs_exist_and_write_output_remains_last():
    assert hasattr(ost.Output, "translated_json")
    assert hasattr(ost.Output, "rendered_output")
    # write_output must remain the logical last output (used for the progress bar).
    assert max(ost.Output) == ost.Output.write_output
    assert ost.Output.inpainted_output < ost.Output.translated_json
    assert ost.Output.translated_json < ost.Output.rendered_output < ost.Output.write_output


def test_output_to_step_mapping():
    assert ost.output_to_step[ost.Output.translated_json] == ost.Step.translator
    assert ost.output_to_step[ost.Output.rendered_output] == ost.Step.renderer


def test_step_to_output_mapping():
    assert ost.step_to_output[ost.Step.translator] == (ost.Output.translated_json,)
    assert ost.step_to_output[ost.Step.renderer] == (ost.Output.rendered_output,)


def test_get_output_representing_step():
    assert ost.get_output_representing_step(ost.Step.translator) == ost.Output.translated_json
    assert ost.get_output_representing_step(ost.Step.renderer) == ost.Output.rendered_output


def test_output_path_generator_new_paths(tmp_path):
    gen = ost.OutputPathGenerator(
        original_path=Path("/imgs/page.png"),
        output_dir=tmp_path,
        uuid_source="abcd",
    )
    assert gen.translated_json.name == "abcd_page#translated.json"
    assert gen.rendered.name == "abcd_page_rendered.png"
    # for_output routes the new outputs to the new paths.
    assert gen.for_output(ost.Output.translated_json) == gen.translated_json
    assert gen.for_output(ost.Output.rendered_output) == gen.rendered


def test_existing_outputs_unaffected(tmp_path):
    gen = ost.OutputPathGenerator(Path("/imgs/p.png"), tmp_path, uuid_source="u")
    # Spot-check that pre-existing output paths still resolve.
    assert gen.for_output(ost.Output.masked_output) == gen.clean
    assert gen.for_output(ost.Output.inpainted_output) == gen.clean_inpaint
