import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import application_review as review


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.archive = self.root / 'documents/applications/test_ai_engineer'
        self.archive.mkdir(parents=True)
        self.resume = self.root / 'resume.pdf'
        self.resume.write_bytes(b'%PDF-1.7\nfixture')
        self.answers = self.archive / 'form_answers.json'
        self.answers.write_text(json.dumps({'fields': [
            {'label': 'Email', 'value': 'test@example.test', 'source': 'user'}],
            'unresolved': []}), encoding='utf-8')
        self.packet = self.archive / 'submission_review.json'

    def prepare(self, **overrides):
        args = dict(root=self.root, output=self.packet, company='Test', role='AI Engineer',
                    job_url='https://example.test/job/1',
                    application_url='https://example.test/job/1/apply', resume=self.resume,
                    cover=None, answers=self.answers)
        args.update(overrides)
        return review.prepare(**args)

    def test_approval_required_and_valid_approval(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'approval'):
            review.check(self.root, self.packet, True)
        review.approve(self.root, self.packet, 'Submit this reviewed application')
        self.assertEqual(review.check(self.root, self.packet, True)['status'], 'approved')

    def test_modified_attachment_invalidates_approval(self):
        self.prepare()
        review.approve(self.root, self.packet, 'Submit this application')
        self.resume.write_bytes(b'%PDF-1.7\nchanged')
        with self.assertRaisesRegex(ValueError, 'Attachment changed'):
            review.check(self.root, self.packet, True)

    def test_modified_answers_invalidates_approval(self):
        self.prepare()
        review.approve(self.root, self.packet, 'Submit this application')
        self.answers.write_text('{"fields": [], "unresolved": []}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Answers changed'):
            review.check(self.root, self.packet, True)

    def test_modified_destination_invalidates_approval(self):
        self.prepare()
        review.approve(self.root, self.packet, 'Submit this application')
        data = json.loads(self.packet.read_text())
        data['application_url'] = 'https://other.example.test/apply'
        self.packet.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Reviewed content changed'):
            review.check(self.root, self.packet, True)

    def test_unknown_answers_block_approval(self):
        self.answers.write_text('{"fields": [], "unresolved": ["Salary?"]}')
        self.prepare()
        with self.assertRaises(ValueError):
            review.approve(self.root, self.packet, 'Submit')

    def test_regeneration_resets_approval(self):
        self.prepare()
        review.approve(self.root, self.packet, 'Submit')
        self.assertIsNone(self.prepare()['approval'])
        with self.assertRaises(ValueError):
            review.check(self.root, self.packet, True)

    def test_empty_source_and_duplicate_labels_rejected(self):
        self.answers.write_text('{"fields": [{"label":"Name","value":"A","source":""}],"unresolved":[]}')
        with self.assertRaises(ValueError):
            self.prepare()
        self.answers.write_text('{"fields": [{"label":"Name","value":"A","source":"user"},{"label":"Name","value":"B","source":"user"}],"unresolved":[]}')
        with self.assertRaises(ValueError):
            self.prepare()

    def test_path_escape_and_non_pdf_rejected(self):
        with self.assertRaises(ValueError):
            self.prepare(output=self.root.parent / 'submission_review.json')
        self.resume.write_bytes(b'not a PDF')
        with self.assertRaises(ValueError):
            self.prepare()

    def test_credentials_in_destination_rejected(self):
        with self.assertRaises(ValueError):
            self.prepare(application_url='https://user:password@example.test/apply')


if __name__ == '__main__':
    unittest.main()
