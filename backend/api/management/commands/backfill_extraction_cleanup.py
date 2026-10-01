from django.core.management.base import BaseCommand
from django.db import transaction

from api.classification import classify_prompt_text, normalize_text
from api.models import Extraction
from api.optimizer import optimize_prompt
from api.text_cleaning import clean_extracted_text


class Command(BaseCommand):
    help = 'Re-clean completed extraction records and regenerate classification and optimization fields.'

    def handle(self, *args, **options):
        updated = 0
        skipped = 0

        for extraction in Extraction.objects.filter(status=Extraction.Status.COMPLETED).iterator():
            source_text = extraction.raw_ocr_text or extraction.extracted_text
            cleaned_text = clean_extracted_text(source_text)
            classification = classify_prompt_text(normalize_text(cleaned_text))
            optimization = (
                optimize_prompt(cleaned_text, classification.matched_signals)
                if classification.label != 'not_prompt'
                else None
            )

            changed = (
                extraction.extracted_text != cleaned_text
                or extraction.classification_label != classification.label
                or extraction.classification_score != classification.score
                or extraction.classification_confidence != classification.confidence
                or extraction.optimized_prompt != (optimization.optimized_prompt if optimization else '')
                or extraction.optimizer_template != (optimization.template if optimization else '')
                or extraction.optimizer_components != (optimization.components if optimization else {})
            )
            if not changed:
                skipped += 1
                continue

            with transaction.atomic():
                extraction.extracted_text = cleaned_text
                extraction.classification_label = classification.label
                extraction.classification_score = classification.score
                extraction.classification_confidence = classification.confidence
                extraction.matched_signals = [
                    {
                        'text': signal.text,
                        'category': signal.category,
                        'weight': signal.weight,
                        'polarity': signal.polarity,
                    }
                    for signal in classification.matched_signals
                ]
                extraction.classifier_version = classification.classifier_version
                extraction.optimized_prompt = optimization.optimized_prompt if optimization else ''
                extraction.optimizer_template = optimization.template if optimization else ''
                extraction.optimizer_components = optimization.components if optimization else {}
                extraction.optimizer_version = optimization.optimizer_version if optimization else ''
                extraction.save(update_fields=[
                    'extracted_text',
                    'classification_label',
                    'classification_score',
                    'classification_confidence',
                    'matched_signals',
                    'classifier_version',
                    'optimized_prompt',
                    'optimizer_template',
                    'optimizer_components',
                    'optimizer_version',
                    'updated_at',
                ])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} extraction(s); skipped {skipped}.'))
