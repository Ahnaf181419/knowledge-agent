import trafilatura
from typing import Optional
from app.logger import logger


class TextExtractor:
    @staticmethod
    def extract_from_html(html: str, output_format: str = 'markdown') -> Optional[str]:
        try:
            if output_format == 'markdown':
                result = trafilatura.extract(
                    html,
                    output_format='markdown',
                    include_comments=False,
                    include_images=False,
                    include_tables=True
                )
            elif output_format == 'txt':
                result = trafilatura.extract(
                    html,
                    output_format='txt',
                    include_comments=False
                )
            elif output_format == 'json':
                result = trafilatura.extract(
                    html,
                    output_format='json',
                    include_comments=False
                )
            else:
                result = trafilatura.extract(
                    html,
                    output_format='markdown',
                    include_comments=False
                )

            if result:
                logger.info(f"Text extraction successful ({output_format})")
            else:
                logger.warning("Text extraction returned empty result")

            return result

        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return None

    @staticmethod
    def extract_with_metadata(html: str) -> Optional[dict]:
        try:
            result = trafilatura.extract(
                html,
                output_format='json',
                include_comments=False,
                include_images=False,
                with_metadata=True
            )

            if result:
                import json
                return json.loads(result)

            return None

        except Exception as e:
            logger.error(f"Text extraction with metadata error: {str(e)}")
            return None

    @staticmethod
    def get_metadata(html: str) -> Optional[dict]:
        try:
            metadata = trafilatura.metadata.extract_metadata(html)
            if metadata:
                return {
                    'title': metadata.get('title'),
                    'author': metadata.get('author'),
                    'date': metadata.get('date'),
                    'description': metadata.get('description'),
                    'sitename': metadata.get('sitename')
                }
            return None
        except Exception as e:
            logger.error(f"Metadata extraction error: {str(e)}")
            return None


def extract_text(html: str, output_format: str = 'markdown') -> Optional[str]:
    return TextExtractor.extract_from_html(html, output_format)
