from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .chunker import MarkdownPreprocessor, AtomicUnitDetector, MarkdownChunker, LLMHeadingEnhancer


class MdTextChunkerTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Chunk markdown text using hybrid strategy with metadata.
        Optimized for MinerU-parsed documents but supports any markdown.
        Supports optional LLM-based heading hierarchy enhancement.
        """
        try:
            # Get parameters
            input_text = tool_parameters.get("input_text", "")
            if not input_text:
                yield self.create_text_message("Error: input_text is required")
                return

            # Get optional file title
            file_title = tool_parameters.get("file_title", "")

            # Get parameters
            remove_extra_spaces = tool_parameters.get("remove_extra_spaces", False)
            remove_urls_emails = tool_parameters.get("remove_urls_emails", False)

            # Fixed max_chunk_length (not configurable)
            max_chunk_length = 2000

            # LLM enhancement parameters
            enable_llm_enhancement = tool_parameters.get("enable_llm_enhancement", False)
            llm_api_base = tool_parameters.get("llm_api_base", "")
            llm_api_key = tool_parameters.get("llm_api_key", "")
            llm_model = tool_parameters.get("llm_model", "gpt-3.5-turbo")

            # Phase 1: Preprocess (convert literal \n, clean text)
            preprocessor = MarkdownPreprocessor(
                remove_extra_spaces=remove_extra_spaces,
                remove_urls_emails=remove_urls_emails,
            )
            processed_text = preprocessor.preprocess(input_text)

            # Phase 2: Optional LLM-based heading enhancement
            # (must come AFTER preprocessing to get proper newlines)
            if enable_llm_enhancement:
                if not llm_api_base or not llm_api_key:
                    yield self.create_text_message(
                        "Error: LLM enhancement requires llm_api_base and llm_api_key"
                    )
                    return

                try:
                    enhancer = LLMHeadingEnhancer(
                        api_base=llm_api_base,
                        api_key=llm_api_key,
                        model=llm_model
                    )
                    processed_text = enhancer.enhance_headings(processed_text)
                except Exception as e:
                    # Log error but continue with original text
                    yield self.create_text_message(
                        f"Warning: LLM enhancement failed ({str(e)}), using original text"
                    )

            # Phase 3: Detect atomic units (always preserve tables and formulas)
            detector = AtomicUnitDetector(
                preserve_tables=True,
                preserve_code_blocks=False,  # Don't preserve code blocks
                preserve_formulas=True,
            )
            atomic_units = detector.detect(processed_text)

            # Phase 4: Chunk using hybrid strategy with heading_level=1
            chunker = MarkdownChunker(
                strategy="hybrid",
                max_chunk_length=max_chunk_length,
                chunk_overlap_length=0,  # No overlap
                heading_level=1,
                atomic_units=atomic_units,
            )
            chunk_tuples = chunker.chunk(processed_text)

            # Phase 5: Add metadata to each chunk
            chunks_with_metadata = []
            for chunk_text, heading_path in chunk_tuples:
                # Build metadata XML
                metadata = self._build_metadata(file_title, heading_path)

                # Prepend metadata to chunk
                chunk_with_metadata = f"{metadata}\n{chunk_text}"
                chunks_with_metadata.append(chunk_with_metadata)

            # Phase 6: Return result in Dify standard format
            # Output is GeneralStructureChunk: list of strings
            yield self.create_variable_message("result", chunks_with_metadata)

        except Exception as e:
            yield self.create_text_message(f"Error during chunking: {str(e)}")

    def _build_metadata(self, file_title: str, heading_path: list[str]) -> str:
        """
        Build metadata XML string.

        Args:
            file_title: Optional file title
            heading_path: List of heading titles in hierarchy

        Returns:
            Metadata XML string
        """
        metadata_parts = []

        if file_title:
            metadata_parts.append(f"<Title>{file_title}</Title>")

        if heading_path:
            # Join heading path with " > " separator
            path_str = " > ".join(heading_path)
            metadata_parts.append(f"<Headings>{path_str}</Headings>")

        if metadata_parts:
            return f"<metadata>\n{chr(10).join(metadata_parts)}\n</metadata>"
        else:
            return "<metadata>\n</metadata>"
