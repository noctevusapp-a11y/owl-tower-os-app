"""Scope tokens: which inclusion token of a sibling delivers what a work item excludes under another name.

A work item that excludes 'gypsum_board' (it only frames the wall) is complemented, in an assembly, by the sibling that includes
'board_material'. The assembly must therefore NOT list 'gypsum_board' as excluded (a reader would add the board a second time), and
a child's exclusion is only surfaced on the assembly when no sibling inclusion covers it. Tokens are our own vocabulary; extend this
map when a new work item introduces an exclusion that another work item prices under a different token name.
"""
from __future__ import annotations

from typing import Iterable

# excluded token -> inclusion tokens (of any work item) that price the same thing; ONE of them in the assembly's inclusions is enough
SCOPE_COVERS: dict[str, frozenset[str]] = {
    "gypsum_board": frozenset({"board_material"}),
    "board_hanging": frozenset({"cut_hang_and_fasten_labor"}),
    "taping_and_finishing": frozenset({"joint_compound_material", "taping_finishing_and_sanding_labor"}),
    "primer": frozenset({"primer_material"}),
    "primer_and_paint": frozenset({"primer_material", "wall_finish_material", "ceiling_finish_material"}),
    "finish_coats": frozenset({"wall_finish_material", "ceiling_finish_material"}),
    "framing": frozenset({"stud_and_plate_materials", "stud_and_track_materials"}),
    "sheathing": frozenset({"panel_material"}),
    "blocking": frozenset({"blocking_materials"}),
    "blocking_backing": frozenset({"blocking_materials"}),
    "blocking_and_backing": frozenset({"blocking_materials"}),
    "curing": frozenset({"curing_compound_material"}),
    "concrete_placing_and_finishing": frozenset({"placing_screeding_finishing_labor", "placing_and_vibrating_labor"}),
    "indoor_unit_and_coil": frozenset({"furnace_equipment", "coil_equipment"}),
    "outdoor_unit": frozenset({"condenser_equipment"}),
    "thermostat_and_controls": frozenset({"thermostat_material"}),
    "ductwork": frozenset({"duct_material"}),
    "anchor_bolts": frozenset({"anchor_bolt_material"}),
}


def scope_covered(token: str, included: Iterable[str]) -> bool:
    """True when `token` (an exclusion) is priced by the given inclusions, under the same name or under a mapped synonym."""
    inc = set(included)
    return token in inc or bool(SCOPE_COVERS.get(token, frozenset()) & inc)
