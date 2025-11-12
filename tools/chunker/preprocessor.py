"""
Preprocessor for MinerU-parsed markdown documents.
Enhanced with best practices from official Dify chunk plugins.
"""

import re


class MarkdownPreprocessor:
    """
    Preprocessor for MinerU markdown documents.
    Handles literal newline conversion, text normalization, and cleaning.
    """

    def __init__(
        self,
        remove_extra_spaces: bool = False,
        remove_urls_emails: bool = False,
    ):
        """
        Initialize preprocessor.

        Args:
            remove_extra_spaces: Whether to normalize whitespace
            remove_urls_emails: Whether to remove URLs and email addresses
        """
        self.remove_extra_spaces = remove_extra_spaces
        self.remove_urls_emails = remove_urls_emails

    def preprocess(self, text: str) -> str:
        """
        Preprocess markdown text.

        Args:
            text: Raw markdown text from MinerU

        Returns:
            Preprocessed text
        """
        # Step 0: Remove invalid characters (control chars, BOM, invalid Unicode)
        text = self._remove_invalid_characters(text)

        # Step 1: Convert literal \n to actual newlines
        text = self._convert_literal_newlines(text)

        # Step 2: Clean URLs and emails if requested (smart mode preserves Markdown images)
        if self.remove_urls_emails:
            text = self._remove_urls_and_emails(text)

        # Step 3: Normalize whitespace if requested (comprehensive Unicode handling)
        if self.remove_extra_spaces:
            text = self._normalize_whitespace(text)

        # Step 4: Clean common MinerU artifacts
        text = self._clean_artifacts(text)

        # Step 5: Clean leading punctuation
        text = self._clean_leading_punctuation(text)

        return text

    def _remove_invalid_characters(self, text: str) -> str:
        """
        Remove invalid characters (control chars, BOM, invalid Unicode).
        Based on official Dify chunk plugin best practices.

        Args:
            text: Input text

        Returns:
            Text with invalid characters removed
        """
        # Normalize special bracket patterns
        text = re.sub(r"<\|", "<", text)
        text = re.sub(r"\|>", ">", text)

        # Remove control characters (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, 0x7F)
        # Also removes 0xEFBFBE (invalid UTF-8 sequence)
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]", "", text)

        # Remove Unicode U+FFFE (non-character)
        text = re.sub("\ufffe", "", text)

        return text

    def _convert_literal_newlines(self, text: str) -> str:
        """
        Convert literal \n strings to actual newline characters.
        MinerU outputs files with literal backslash-n instead of actual newlines.

        Args:
            text: Text with literal \n

        Returns:
            Text with actual newlines
        """
        # Replace literal \n with actual newline
        # Be careful not to replace \\n (escaped backslash + n)
        text = text.replace("\\n", "\n")
        return text

    def _remove_urls_and_emails(self, text: str) -> str:
        """
        Remove URLs and email addresses from text.
        Smart mode: Preserves Markdown image URLs while removing other URLs.
        Based on official Dify chunk plugin best practices.

        Args:
            text: Input text

        Returns:
            Text with URLs and emails removed (except Markdown images)
        """
        # Remove email addresses first
        email_pattern = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
        text = re.sub(email_pattern, "", text)

        # Smart URL removal: Preserve Markdown image URLs
        # Step 1: Find and temporarily replace Markdown image URLs
        markdown_image_pattern = r"!\[.*?\]\((https?://[^\s)]+)\)"
        placeholders = []

        def replace_with_placeholder(match):
            url = match.group(1)
            placeholder = f"__MARKDOWN_IMAGE_URL_{len(placeholders)}__"
            placeholders.append(url)
            return f"![image]({placeholder})"

        text = re.sub(markdown_image_pattern, replace_with_placeholder, text)

        # Step 2: Remove all remaining URLs
        url_pattern = r"https?://[^\s)]+"
        text = re.sub(url_pattern, "", text)

        # Step 3: Restore Markdown image URLs
        for i, url in enumerate(placeholders):
            text = text.replace(f"__MARKDOWN_IMAGE_URL_{i}__", url)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text with comprehensive Unicode support.
        - Replace multiple spaces/tabs with single space
        - Replace 3+ newlines with 2 newlines
        - Remove trailing spaces
        - Handles all Unicode whitespace characters

        Note: We preserve formulas and tables, so we don't normalize inside them.
        Based on official Dify chunk plugin best practices.

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Temporarily protect formulas and tables
        protected_blocks = []
        placeholder_template = "<<<PROTECTED_BLOCK_{}>>>"

        # Extract and protect display math ($$...$$)
        def protect_display_math(match):
            idx = len(protected_blocks)
            protected_blocks.append(match.group(0))
            return placeholder_template.format(idx)

        text = re.sub(r"\$\$[\s\S]*?\$\$", protect_display_math, text)

        # Extract and protect inline math ($...$)
        def protect_inline_math(match):
            idx = len(protected_blocks)
            protected_blocks.append(match.group(0))
            return placeholder_template.format(idx)

        text = re.sub(r"\$[^$]+\$", protect_inline_math, text)

        # Extract and protect HTML tables
        def protect_table(match):
            idx = len(protected_blocks)
            protected_blocks.append(match.group(0))
            return placeholder_template.format(idx)

        text = re.sub(r"<table>[\s\S]*?</table>", protect_table, text, flags=re.IGNORECASE)

        # Now normalize whitespace in unprotected text
        # Replace 3+ consecutive newlines with 2 newlines (keep paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace multiple spaces/tabs/Unicode spaces with single space
        # Comprehensive Unicode whitespace pattern from official plugins:
        # \t \f \r \x20 (space) \u00a0 (non-breaking space) \u1680 (Ogham space)
        # \u180e (Mongolian vowel separator) \u2000-\u200a (various width spaces)
        # \u202f (narrow no-break space) \u205f (medium mathematical space)
        # \u3000 (ideographic space - CJK)
        pattern = r"[\t\f\r\x20\u00a0\u1680\u180e\u2000-\u200a\u202f\u205f\u3000]{2,}"
        text = re.sub(pattern, " ", text)

        # Remove trailing spaces at end of lines
        text = re.sub(r" +\n", "\n", text)

        # Restore protected blocks
        for idx, block in enumerate(protected_blocks):
            text = text.replace(placeholder_template.format(idx), block)

        return text

    def _clean_artifacts(self, text: str) -> str:
        """
        Clean common MinerU parsing artifacts.

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Remove standalone page numbers (single digit or double digit on own line)
        # Pattern: \n followed by 1-3 digits followed by \n
        text = re.sub(r"\n\d{1,3}\n(?=\n)", "\n", text)

        # Remove excessive dots from table of contents
        # Pattern: multiple dots (.....) often used as leaders in ToC
        text = re.sub(r"\.{5,}", "", text)

        return text

    def _clean_leading_punctuation(self, text: str) -> str:
        """
        Clean leading punctuation from paragraphs.
        Based on official Dify chunk plugin best practices.

        Args:
            text: Input text

        Returns:
            Text with leading punctuation cleaned
        """
        # Split into paragraphs (double newline separated)
        paragraphs = text.split("\n\n")
        cleaned_paragraphs = []

        for para in paragraphs:
            # Remove leading Chinese or English periods
            while para.startswith(".") or para.startswith("。"):
                para = para[1:].strip()

            # Only add non-empty paragraphs
            if para:
                cleaned_paragraphs.append(para)

        return "\n\n".join(cleaned_paragraphs)
