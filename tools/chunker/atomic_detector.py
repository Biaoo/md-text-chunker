"""
Atomic unit detector for identifying indivisible content blocks.
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class AtomicUnit:
    """Represents an indivisible content block."""

    start: int  # Start position in text
    end: int  # End position in text
    type: str  # Type: "formula_block", "table", "table_with_caption", "code_block"
    content: str  # The actual content


class AtomicUnitDetector:
    """
    Detects atomic units that should not be split during chunking.
    """

    def __init__(
        self,
        preserve_tables: bool = True,
        preserve_code_blocks: bool = False,
        preserve_formulas: bool = True,
    ):
        """
        Initialize detector.

        Args:
            preserve_tables: Whether to protect HTML tables
            preserve_code_blocks: Whether to protect code blocks
            preserve_formulas: Whether to protect formula blocks
        """
        self.preserve_tables = preserve_tables
        self.preserve_code_blocks = preserve_code_blocks
        self.preserve_formulas = preserve_formulas

    def detect(self, text: str) -> List[AtomicUnit]:
        """
        Detect all atomic units in text.

        Args:
            text: Preprocessed markdown text

        Returns:
            List of atomic units sorted by start position
        """
        units = []

        if self.preserve_formulas:
            units.extend(self._detect_formula_blocks(text))

        if self.preserve_tables:
            units.extend(self._detect_tables(text))

        if self.preserve_code_blocks:
            units.extend(self._detect_code_blocks(text))

        # Sort by start position
        units.sort(key=lambda u: u.start)

        # Merge overlapping units (shouldn't happen, but just in case)
        units = self._merge_overlapping(units)

        return units

    def _detect_formula_blocks(self, text: str) -> List[AtomicUnit]:
        """
        Detect formula blocks: heading + equation + variable definitions.

        Pattern:
        # N）<title>

        $$
        <equation>
        $$

        式中，
        variable1 definition；
        variable2 definition；

        Args:
            text: Input text

        Returns:
            List of formula block atomic units
        """
        units = []

        # Pattern for formula blocks
        # Matches: # <number>）<text> followed by $$ ... $$ and definitions
        pattern = r"(# \d+[)）][^\n]+\n\n\$\$[\s\S]*?\$\$\n\n(?:式中[，,]?[\s\S]*?)?)(?=\n#|\Z)"

        for match in re.finditer(pattern, text):
            units.append(
                AtomicUnit(
                    start=match.start(),
                    end=match.end(),
                    type="formula_block",
                    content=match.group(0),
                )
            )

        return units

    def _detect_tables(self, text: str) -> List[AtomicUnit]:
        """
        Detect HTML tables, optionally with their captions.

        Args:
            text: Input text

        Returns:
            List of table atomic units
        """
        units = []

        # First, detect tables with captions
        # Pattern: # <heading with 表 or Table> followed by <table>
        caption_pattern = r"(# [^\n]*[表Table][^\n]*\n\n<table>[\s\S]*?</table>)"

        for match in re.finditer(caption_pattern, text, flags=re.IGNORECASE):
            units.append(
                AtomicUnit(
                    start=match.start(),
                    end=match.end(),
                    type="table_with_caption",
                    content=match.group(0),
                )
            )

        # Then detect standalone tables (not already captured)
        table_pattern = r"<table>[\s\S]*?</table>"

        for match in re.finditer(table_pattern, text, flags=re.IGNORECASE):
            # Check if this table is already part of a table_with_caption unit
            is_already_captured = any(
                u.type == "table_with_caption" and u.start <= match.start() < u.end
                for u in units
            )

            if not is_already_captured:
                units.append(
                    AtomicUnit(
                        start=match.start(),
                        end=match.end(),
                        type="table",
                        content=match.group(0),
                    )
                )

        return units

    def _detect_code_blocks(self, text: str) -> List[AtomicUnit]:
        """
        Detect code blocks (fenced or indented).

        Args:
            text: Input text

        Returns:
            List of code block atomic units
        """
        units = []

        # Fenced code blocks (```...```)
        fenced_pattern = r"```[\s\S]*?```"

        for match in re.finditer(fenced_pattern, text):
            units.append(
                AtomicUnit(
                    start=match.start(),
                    end=match.end(),
                    type="code_block",
                    content=match.group(0),
                )
            )

        # Indented code blocks (4 spaces or tab at start of line)
        # This is more complex and prone to false positives, so we skip for now
        # MinerU documents typically don't have indented code blocks

        return units

    def _merge_overlapping(self, units: List[AtomicUnit]) -> List[AtomicUnit]:
        """
        Merge overlapping atomic units.

        Args:
            units: List of atomic units (sorted by start position)

        Returns:
            List with overlapping units merged
        """
        if not units:
            return []

        merged = [units[0]]

        for current in units[1:]:
            last = merged[-1]

            # Check if current overlaps with last
            if current.start < last.end:
                # Merge: extend last to include current
                # Note: content will be the combined content from both units
                merged_content = last.content
                if current.end > last.end:
                    # Append the part of current that extends beyond last
                    merged_content = merged_content + current.content[last.end - current.start :]

                merged[-1] = AtomicUnit(
                    start=last.start,
                    end=max(last.end, current.end),
                    type=f"{last.type}+{current.type}",  # Combined type
                    content=merged_content,
                )
            else:
                merged.append(current)

        return merged

    def is_inside_atomic_unit(self, position: int, units: List[AtomicUnit]) -> bool:
        """
        Check if a position is inside any atomic unit.

        Args:
            position: Position to check
            units: List of atomic units

        Returns:
            True if position is inside an atomic unit
        """
        return any(unit.start <= position < unit.end for unit in units)

    def get_atomic_unit_at(self, position: int, units: List[AtomicUnit]) -> AtomicUnit | None:
        """
        Get the atomic unit containing a position.

        Args:
            position: Position to check
            units: List of atomic units

        Returns:
            Atomic unit containing position, or None
        """
        for unit in units:
            if unit.start <= position < unit.end:
                return unit
        return None
