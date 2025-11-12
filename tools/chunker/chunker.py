"""
Main markdown chunker implementation with support for multiple heading levels.
"""

import re
from typing import List, Tuple
from .atomic_detector import AtomicUnit


class MarkdownChunker:
    """
    Markdown chunker with support for semantic, fixed, and hybrid strategies.
    Supports multiple heading levels (H1-H6), not just H1.
    """

    def __init__(
        self,
        strategy: str = "hybrid",
        max_chunk_length: int = 2000,
        chunk_overlap_length: int = 100,
        heading_level: int = 1,
        atomic_units: List[AtomicUnit] = None,
    ):
        """
        Initialize chunker.

        Args:
            strategy: Chunking strategy ("semantic", "fixed", "hybrid")
            max_chunk_length: Maximum chunk size in characters
            chunk_overlap_length: Overlap between chunks
            heading_level: Heading level to split on (1-6)
            atomic_units: List of atomic units to protect
        """
        self.strategy = strategy
        self.max_chunk_length = max_chunk_length
        self.chunk_overlap_length = chunk_overlap_length
        self.heading_level = heading_level
        self.atomic_units = atomic_units or []

    def chunk(self, text: str) -> List[Tuple[str, List[str]]]:
        """
        Chunk text according to configured strategy.

        Args:
            text: Preprocessed markdown text

        Returns:
            List of tuples (chunk_text, heading_path) where heading_path is a list of heading titles
        """
        if self.strategy == "semantic":
            chunks = self._semantic_chunking(text)
        elif self.strategy == "fixed":
            chunks = self._fixed_chunking(text)
        else:  # hybrid
            chunks = self._hybrid_chunking(text)

        # Note: chunks now contain tuples of (text, heading_path)
        # Post-process: add overlap if configured (not supported in current version)
        # if self.chunk_overlap_length > 0:
        #     chunks = self._add_overlap(chunks)

        # Final cleanup - filter out empty chunks
        chunks = [(c[0].strip(), c[1]) for c in chunks if c[0].strip()]

        return chunks

    def _semantic_chunking(self, text: str) -> List[Tuple[str, List[str]]]:
        """
        Split by recognizing all heading levels (H1-H6).
        Chunks based on heading hierarchy - splits at specified heading level or higher.

        Args:
            text: Input text

        Returns:
            List of tuples (chunk_text, heading_path)
        """
        # Find ALL headings (H1-H6) with their levels
        all_headings = []
        heading_pattern = r"(?:^|\n)(#{1,6}) ([^\n]+)"

        for match in re.finditer(heading_pattern, text):
            level = len(match.group(1))
            title = match.group(2).strip()
            position = match.start()
            all_headings.append({
                'level': level,
                'title': title,
                'position': position,
                'match': match
            })

        if not all_headings:
            # No headings found, return whole text as one chunk with empty path
            if text.strip():
                return [(text.strip(), [])]
            else:
                return []

        # Filter headings: only split at self.heading_level or higher (smaller level number)
        split_headings = [h for h in all_headings if h['level'] <= self.heading_level]

        if not split_headings:
            # No headings at split level, return whole text with extracted heading path
            heading_path = self._extract_heading_path(text)
            return [(text.strip(), heading_path)]

        chunks = []

        # Content before first split heading
        first_split = split_headings[0]
        if first_split['position'] > 0:
            before_content = text[: first_split['position']].strip()
            if before_content:
                # Extract any headings from content before first split
                heading_path = self._extract_heading_path(before_content)
                chunks.append((before_content, heading_path))

        # Use a stack to track heading hierarchy across ALL headings (H1-H6)
        heading_stack = []
        all_heading_index = 0  # Track position in all_headings

        # Process each split heading and its content
        for i, heading_info in enumerate(split_headings):
            # Update the heading stack by processing all headings up to and including this split heading
            # This ensures we capture the full hierarchy (H1 > H2 > H3, etc.)
            while all_heading_index < len(all_headings):
                current_heading = all_headings[all_heading_index]

                # Stop if we've reached beyond the current split heading
                if current_heading['position'] > heading_info['position']:
                    break

                # Update stack with this heading
                level = current_heading['level']
                title = current_heading['title']

                # Truncate title to 30 characters
                if len(title) > 30:
                    title = title[:30]

                # Maintain the stack: remove headings at same or deeper levels
                while len(heading_stack) >= level:
                    heading_stack.pop()

                # Add current heading to stack
                heading_stack.append(title)

                all_heading_index += 1

            # Start position is the heading itself
            start = heading_info['position']
            # If there's a newline before heading, skip it
            if start > 0 and text[start] == "\n":
                start += 1

            # End position is either the start of next split heading or end of text
            if i + 1 < len(split_headings):
                end = split_headings[i + 1]['position']
                # Don't include the newline before next heading
                while end > start and text[end - 1] == "\n":
                    end -= 1
            else:
                end = len(text)

            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                # Use the current heading stack as the heading path
                # This gives us the complete hierarchy including parent headings
                heading_path = list(heading_stack)
                chunks.append((chunk, heading_path))

        return chunks

    def _fixed_chunking(self, text: str) -> List[Tuple[str, List[str]]]:
        """
        Split by size with boundary awareness.
        Respects atomic units and tries to split at natural boundaries.

        Args:
            text: Input text

        Returns:
            List of tuples (chunk_text, heading_path)
        """
        chunks = []
        start = 0

        while start < len(text):
            # Determine chunk end
            end = min(start + self.max_chunk_length, len(text))

            # Find best split point before end
            split_pos = self._find_best_split_point(text, start, end)

            # Extract chunk
            chunk = text[start:split_pos].strip()
            if chunk:
                # Extract heading path from this chunk
                heading_path = self._extract_heading_path(chunk)
                chunks.append((chunk, heading_path))

            # Move to next chunk
            start = split_pos

        return chunks

    def _hybrid_chunking(self, text: str) -> List[Tuple[str, List[str]]]:
        """
        Semantic chunking with size constraints.
        Split by headings, but further split if sections are too large.

        Args:
            text: Input text

        Returns:
            List of tuples (chunk_text, heading_path)
        """
        # First, split by headings (returns tuples)
        sections = self._semantic_chunking(text)

        chunks = []

        for section_text, heading_path in sections:
            if len(section_text) <= self.max_chunk_length:
                # Section fits, add as-is
                chunks.append((section_text, heading_path))
            else:
                # Section too large, need to split further
                sub_chunks = self._split_large_section(section_text, heading_path)
                chunks.extend(sub_chunks)

        return chunks

    def _split_large_section(self, section: str, heading_path: List[str]) -> List[Tuple[str, List[str]]]:
        """
        Split a large section that exceeds max_chunk_length.
        Respects atomic units and tries to split at paragraph boundaries.

        Args:
            section: Large section text
            heading_path: Heading path for this section

        Returns:
            List of tuples (chunk_text, heading_path)
        """
        chunks = []
        start = 0

        while start < len(section):
            # Determine chunk end
            end = min(start + self.max_chunk_length, len(section))

            # Find best split point
            split_pos = self._find_best_split_point(section, start, end)

            # Handle case where split_pos hasn't moved (atomic unit too large)
            if split_pos == start:
                # Find the atomic unit and include it entirely
                atomic_unit = self._get_atomic_unit_at(start, section)
                if atomic_unit:
                    split_pos = atomic_unit.end
                else:
                    # No atomic unit, force split at end
                    split_pos = end

            # Extract chunk
            chunk = section[start:split_pos].strip()
            if chunk:
                # All sub-chunks inherit the same heading path
                chunks.append((chunk, heading_path))

            # Move to next chunk
            start = split_pos

        return chunks

    def _find_best_split_point(self, text: str, start: int, end: int) -> int:
        """
        Find the best position to split text between start and end.
        Priority:
        1. Before a heading (highest priority)
        2. At a paragraph break (\\n\\n)
        3. At a sentence end (。！？. ! ?)
        4. At end (last resort)

        Respects atomic unit boundaries.

        Args:
            text: Full text
            start: Start position
            end: Desired end position

        Returns:
            Best split position
        """
        # Don't split inside atomic units
        # Check if there's an atomic unit spanning across end
        for unit in self.atomic_units:
            # If unit starts before end and ends after end, we can't split at end
            if unit.start < end <= unit.end:
                # Move end back to before this atomic unit
                end = unit.start
                break

        # If end is now <= start, we need to include the whole atomic unit
        if end <= start:
            # Find the atomic unit and return its end
            for unit in self.atomic_units:
                if unit.start <= start < unit.end:
                    return unit.end
            # Shouldn't happen, but return end anyway
            return end

        # Now find best split point within [start, end]
        search_text = text[start:end]

        # Priority 1: Before a heading
        # Look for any heading (H1-H6) in reverse
        for level in range(1, 7):
            heading_pattern = r"\n#{" + str(level) + r"} "
            matches = list(re.finditer(heading_pattern, search_text))
            if matches:
                # Take the last heading
                last_match = matches[-1]
                return start + last_match.start() + 1  # +1 to skip the \n

        # Priority 2: Paragraph break
        para_breaks = [m.start() for m in re.finditer(r"\n\n", search_text)]
        if para_breaks:
            # Take the last paragraph break
            return start + para_breaks[-1] + 2  # +2 to skip \n\n

        # Priority 3: Sentence end
        # Look for Chinese or English sentence endings
        sentence_ends = [
            m.end() for m in re.finditer(r"[。！？.!?]\s*", search_text)
        ]
        if sentence_ends:
            # Take the last sentence end
            return start + sentence_ends[-1]

        # Last resort: split at end
        return end

    def _get_atomic_unit_at(self, position: int, _text: str) -> AtomicUnit | None:
        """
        Get atomic unit at position (within text context).

        Args:
            position: Position in text
            _text: Text context (might be a subsection) - unused but kept for API compatibility

        Returns:
            Atomic unit at position, or None
        """
        # Note: This is a simplified version
        # In practice, atomic unit positions are relative to full text
        # For subsections, we'd need to adjust positions
        for unit in self.atomic_units:
            if unit.start <= position < unit.end:
                return unit
        return None

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """
        Add overlap between consecutive chunks.

        Args:
            chunks: List of chunks

        Returns:
            Chunks with overlap added
        """
        if len(chunks) <= 1:
            return chunks

        result = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]

            # Get suffix of previous chunk
            overlap_text = self._get_suffix(prev_chunk, self.chunk_overlap_length)

            # Prepend to current chunk
            result.append(overlap_text + "\n\n" + curr_chunk)

        return result

    def _get_suffix(self, text: str, length: int) -> str:
        """
        Get the last `length` characters of text, preferably at a sentence boundary.

        Args:
            text: Input text
            length: Desired suffix length

        Returns:
            Suffix text
        """
        if len(text) <= length:
            return text

        # Get last `length` chars
        suffix = text[-length:]

        # Try to start at a sentence boundary
        # Look for sentence end in first 20% of suffix
        search_len = min(len(suffix) // 5, 50)
        search_area = suffix[:search_len]

        sentence_ends = [m.end() for m in re.finditer(r"[。！？.!?]\s+", search_area)]
        if sentence_ends:
            # Start from last sentence end found
            return suffix[sentence_ends[-1]:]

        # Otherwise, try to start after a space
        first_space = suffix.find(" ")
        if first_space > 0 and first_space < search_len:
            return suffix[first_space + 1:]

        # Last resort: return as-is
        return suffix

    def _extract_heading_path(self, chunk: str) -> List[str]:
        """
        Extract heading hierarchy from the chunk using a stack-based approach.
        Returns the heading path up to and including the FIRST heading in the chunk.
        This represents the primary context of the chunk.

        Args:
            chunk: Chunk text that may contain headings

        Returns:
            List of heading titles (max 30 chars each) representing the hierarchy
        """
        # Use a stack to maintain the heading hierarchy
        heading_stack = []

        lines = chunk.split('\n')

        # Find the first heading and build its path
        for line in lines:
            line = line.strip()

            # Check if line is a heading
            heading_match = re.match(r'^(#{1,6}) (.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Truncate to 30 characters
                if len(title) > 30:
                    title = title[:30]

                # Maintain the stack: keep only headings at levels < current level
                # This ensures we have the proper ancestor path
                while len(heading_stack) >= level:
                    heading_stack.pop()

                # Add current heading to the stack
                heading_stack.append(title)

                # Return immediately after finding the first heading
                # The stack now contains the complete path to this heading
                return list(heading_stack)

        # No heading found in chunk
        return []
