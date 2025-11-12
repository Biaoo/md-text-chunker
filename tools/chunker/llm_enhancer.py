"""
LLM-based heading hierarchy enhancement module.
Uses OpenAI-compatible API to correct heading levels in markdown documents.
"""

import re
import json
from typing import Optional
import requests
import time


class LLMHeadingEnhancer:
    """
    Uses LLM to analyze and correct heading hierarchy in markdown documents.
    """

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        timeout: int = 300
    ):
        """
        Initialize LLM enhancer.

        Args:
            api_base: OpenAI-compatible API base URL (e.g., "https://api.openai.com/v1/chat/completions")
            api_key: API key for authentication
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def enhance_headings(self, text: str) -> str:
        """
        Enhance heading hierarchy using LLM.

        Args:
            text: Preprocessed markdown text with potentially incorrect heading levels
                  (should already have proper newlines from preprocessing)

        Returns:
            Markdown text with corrected heading levels
        """
        start_time = time.time()

        # Extract all headings from the text
        print(f"Extracting all headings from the text...")
        headings = self._extract_all_headings(text)
        print(f"Extracted {len(headings)} headings")

        if not headings:
            # No headings found, return original text
            return text

        # Call LLM to correct heading levels
        corrected_headings = self._call_llm_for_correction(headings)

        if not corrected_headings:
            # LLM call failed, return original text
            print(f"LLM correction failed, using original text")
            return text

        print(f"Corrected {len(corrected_headings)} headings")
        print(f"Corrected headings: {corrected_headings}")

        # Apply corrections to the text
        corrected_text = self._apply_corrections(text, headings, corrected_headings)

        end_time = time.time()
        print(f"LLM heading enhancement took {end_time - start_time} seconds")

        return corrected_text

    def _extract_all_headings(self, text: str) -> list[dict]:
        """
        Extract all headings from markdown text.
        Also detects potential headings (short single-line paragraphs).

        Returns:
            List of dicts with: {original_level, title, position, original_text, is_potential}
        """
        headings = []

        # First, extract explicit markdown headings (# marked)
        heading_pattern = r'^(#{1,6}) (.+)$'

        for match in re.finditer(heading_pattern, text, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            position = match.start()
            original_text = match.group(0)

            headings.append({
                'original_level': level,
                'title': title,
                'position': position,
                'original_text': original_text,
                'is_potential': False
            })

        # Second, detect potential headings (short single-line text)
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        current_pos = 0

        for para in paragraphs:
            para_stripped = para.strip()

            # Find position of this paragraph in the original text
            para_pos = text.find(para_stripped, current_pos)
            if para_pos == -1:
                current_pos += len(para) + 2  # +2 for \n\n
                continue

            # Check if this paragraph is a single line
            lines = para_stripped.split('\n')
            if len(lines) == 1:
                line = lines[0].strip()

                # Skip if already a markdown heading
                if line.startswith('#'):
                    current_pos = para_pos + len(para_stripped)
                    continue

                # Check if it matches potential heading criteria
                # Chinese: ≤30 characters, English: ≤20 words
                # Apply strict filtering to exclude non-headings
                is_potential_heading = False

                # Filter 1: Exclude lines ending with sentence-ending punctuation
                # Chinese: 。；、
                # English: . ;
                if re.search(r'[。；、.;]$', line):
                    current_pos = para_pos + len(para_stripped)
                    continue

                # Filter 2: Exclude lines that short phrases ending with comma
                if re.search(r'^.{0,5}[，,]\s*$', line):
                    current_pos = para_pos + len(para_stripped)
                    continue

                # Filter 3: Exclude pure symbols or numbers like "(1)", "（5)", etc.
                if re.match(r'^[\(（]?\d+[\)）]?\s*$', line.strip()):
                    current_pos = para_pos + len(para_stripped)
                    continue

                # Filter 4: Exclude lines with too many dots/ellipsis (目录行)
                if line.count('.') > 3 or line.count('．') > 2:
                    current_pos = para_pos + len(para_stripped)
                    continue

                # Filter 5: Exclude lines that are mostly mathematical symbols
                # Count LaTeX math expressions, they usually indicate formulas not headings
                if line.count('$') >= 2 or line.count('\\') > 2:
                    current_pos = para_pos + len(para_stripped)
                    continue

                # Filter 6: Exclude lines ending with colon (usually lead-in text)
                # Pattern: "...包括：" or "...如下："
                if re.search(r'[：:]$', line):
                    current_pos = para_pos + len(para_stripped)
                    continue

                # Now check length criteria
                # Check for Chinese characters
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', line))
                if chinese_chars > 0 and len(line) <= 30:
                    is_potential_heading = True
                # Check for English words
                elif chinese_chars == 0:
                    words = line.split()
                    if 1 <= len(words) <= 20:
                        is_potential_heading = True

                if is_potential_heading:
                    # Check if this position doesn't overlap with existing headings
                    is_duplicate = any(
                        h['position'] == para_pos for h in headings
                    )

                    if not is_duplicate:
                        headings.append({
                            'original_level': 1,  # Default to H1, LLM will correct
                            'title': line,
                            'position': para_pos,
                            'original_text': line,
                            'is_potential': True
                        })

            current_pos = para_pos + len(para_stripped)

        # Sort by position
        headings.sort(key=lambda x: x['position'])

        return headings

    def _call_llm_for_correction(self, headings: list[dict]) -> Optional[list[dict]]:
        """
        Call LLM API to correct heading levels.

        Args:
            headings: List of heading dicts

        Returns:
            List of corrected headings with new levels, or None if failed
        """
        # Build prompt
        prompt = self._build_correction_prompt(headings)

        # Prepare API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a document structure expert. Analyze heading hierarchies and correct heading levels to reflect proper document structure.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.1,
            'max_tokens': 8192
        }

        try:
            # Call API
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()

            # Parse response
            result = response.json()
            llm_response = result['choices'][0]['message']['content']
            print(f"LLM response: {llm_response}")

            # Extract corrected headings from response
            corrected_headings = self._parse_llm_response(llm_response, headings)

            return corrected_headings

        except requests.exceptions.RequestException as e:
            print(f"LLM API call failed: {e}")
            return None
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            print(f"Failed to parse LLM response: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def _build_correction_prompt(self, headings: list[dict]) -> str:
        """
        Build prompt for LLM to correct heading levels.
        """
        # Format headings list
        headings_text = ""
        for i, h in enumerate(headings, 1):
            is_potential = h.get('is_potential', False)
            if is_potential:
                # Potential headings don't have # markers yet
                headings_text += f"{i}. [Potential] {h['title']}\n"
            else:
                prefix = "#" * h['original_level']
                headings_text += f"{i}. {prefix} {h['title']}\n"

        prompt = f"""I have a markdown document with the following headings. Some headings are explicitly marked with # symbols, while others are potential headings (marked with [Potential]) that were detected as short single-line text.

Please analyze the content and semantic relationships of these headings, then assign appropriate heading levels to reflect the proper document structure.

Current headings:
{headings_text}

Please return a JSON array with corrected levels. Each item should have:
- "index": the heading number (1-based)
- "level": the corrected heading level
  - Use 1-6 for actual headings (H1-H6)
  - Use 7 to indicate this is NOT a heading (e.g., it's a sentence fragment, formula reference, or normal text)
- "title": the original title (unchanged)

Pay attention to fundamental logic, such as ensuring adjacent headings at the same level share the same hierarchical structure,
and maintain contextual coherence and logical consistency.

Important: Use level=7 for items that are clearly NOT headings, such as:
- Sentence fragments ending with punctuation (。；：)
- Pure symbols or numbers like "(1)", "式中，"
- Mathematical formulas or variable definitions
- Lead-in phrases like "...包括：" or "...如下："

Example format:
```json
[
  {{"index": 1, "level": 1, "title": "Introduction"}},
  {{"index": 2, "level": 2, "title": "Background"}},
  {{"index": 3, "level": 7, "title": "式中，"}},
  {{"index": 4, "level": 2, "title": "Objectives"}}
]
```

Respond with ONLY the JSON array, no other text."""

        return prompt

    def _parse_llm_response(self, llm_response: str, original_headings: list[dict]) -> Optional[list[dict]]:
        """
        Parse LLM response to extract corrected heading levels.

        Returns:
            List of headings with corrected levels, or None if parsing failed
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', llm_response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON array directly
                json_match = re.search(r'\[[\s\S]*?\]', llm_response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return None

            # Parse JSON
            corrected = json.loads(json_str)

            # Validate and map to original headings
            if len(corrected) != len(original_headings):
                print(f"Warning: LLM returned {len(corrected)} headings, expected {len(original_headings)}")
                return None

            result = []
            for item, original in zip(corrected, original_headings):
                new_level = item.get('level', original['original_level'])
                # Validate level
                # Level 7 means "not a heading" - we'll skip it during application
                if not isinstance(new_level, int) or new_level < 1 or new_level > 7:
                    new_level = original['original_level']

                result.append({
                    'original_level': original['original_level'],
                    'new_level': new_level,
                    'title': original['title'],
                    'position': original['position'],
                    'original_text': original['original_text'],
                    'is_potential': original.get('is_potential', False)
                })

            return result

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Failed to parse LLM response: {e}")
            return None

    def _apply_corrections(self, text: str, original_headings: list[dict], corrected_headings: list[dict]) -> str:
        """
        Apply corrected heading levels to the text.

        Args:
            text: Original text
            original_headings: Original heading information
            corrected_headings: Corrected heading information with new levels

        Returns:
            Text with corrected heading levels
        """
        # Sort by position in forward order (start to end)
        # Track cumulative offset to adjust positions as we make replacements
        corrections = sorted(
            zip(original_headings, corrected_headings),
            key=lambda x: x[0]['position'],
            reverse=False
        )

        result = text
        offset = 0  # Track cumulative length change

        for original, corrected in corrections:
            old_text = original['original_text']
            is_potential = corrected.get('is_potential', False)
            new_level = corrected['new_level']

            # Level 7 means "not a heading" - remove it if it's a potential heading
            if new_level == 7:
                if is_potential:
                    # Remove this potential heading from the text
                    pos = original['position'] + offset
                    result = result[:pos] + result[pos + len(old_text):]
                    offset -= len(old_text)
                # If it was an existing heading, keep it as-is (don't modify)
                continue

            # For potential headings, always add # markers
            # For existing headings, only replace if level changed
            if is_potential or new_level != original['original_level']:
                new_prefix = "#" * new_level
                new_text = f"{new_prefix} {original['title']}"

                # Adjust position by cumulative offset
                pos = original['position'] + offset

                # Replace at the adjusted position
                result = result[:pos] + new_text + result[pos + len(old_text):]

                # Update offset for next replacement
                offset += len(new_text) - len(old_text)

        return result
