#!/usr/bin/env python3
"""Create/check a review packet. This tool never submits an application.

Answers JSON: {"fields": [{"label": "Email", "value": "...", "source": "profile"}],
              "unresolved": []}
Use prepare again after changing any answer, URL, or attachment; approval is invalidated.
"""
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_path(path, root):
    p = Path(path)
    p = (root / p).resolve() if not p.is_absolute() else p.resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError('File must stay inside the repository')
    return p


def https_url(value):
    u = urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        raise ValueError('Use an HTTPS job/application URL without embedded credentials')
    return value


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.review-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def packet_path(path, root):
    p = local_path(path, root)
    archive = (root / 'documents/applications').resolve()
    if not p.is_relative_to(archive) or p.name != 'submission_review.json':
        raise ValueError('Packet must be documents/applications/<archive>/submission_review.json')
    return p


def prepare(root, output, company, role, job_url, application_url, resume, cover, answers):
    if not company.strip() or not role.strip():
        raise ValueError('Company and role are required')
    target = packet_path(output, root)
    answer_path = local_path(answers, root)
    data = json.loads(answer_path.read_text(encoding='utf-8'))
    fields, unresolved = data.get('fields'), data.get('unresolved')
    if not isinstance(fields, list) or not isinstance(unresolved, list):
        raise ValueError('Answers require fields and unresolved lists')
    if not all(isinstance(x, str) and x.strip() for x in unresolved):
        raise ValueError('Unresolved items must be non-empty question strings')
    labels = set()
    for field in fields:
        if not isinstance(field, dict) or any(not isinstance(field.get(k), str) or not field[k].strip()
                                              for k in ('label', 'value', 'source')):
            raise ValueError('Every answer requires non-empty label, value, and factual source')
        if field['label'] in labels:
            raise ValueError('Duplicate field label; include section/index to distinguish repeated fields')
        labels.add(field['label'])
    documents = []
    for kind, filename in [('resume', resume), ('cover_letter', cover)]:
        if not filename:
            continue
        p = local_path(filename, root)
        if p.suffix.lower() != '.pdf' or not p.read_bytes().startswith(b'%PDF-'):
            raise ValueError('Attachments must be existing PDF files; verify their content separately')
        documents.append({'kind': kind, 'path': p.relative_to(root).as_posix(), 'sha256': digest(p)})
    if not documents or documents[0]['kind'] != 'resume':
        raise ValueError('A resume PDF is required')
    packet = {'version': 1, 'status': 'needs_answers' if unresolved else 'awaiting_review',
              'created_at': datetime.now(timezone.utc).isoformat(),
              'company': company, 'role': role, 'job_url': https_url(job_url),
              'application_url': https_url(application_url), 'documents': documents,
              'answers': fields, 'unresolved': unresolved,
              'answers_file': answer_path.relative_to(root).as_posix(),
              'answers_sha256': digest(answer_path),
              'approval': None}
    atomic_json(target, packet)
    return packet


def check(root, packet, require_approval=False):
    path = packet_path(packet, root)
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('version') != 1 or data.get('status') not in ('awaiting_review', 'approved'):
        raise ValueError('Application is not ready for review; resolve missing answers first')
    if data.get('unresolved'):
        raise ValueError('Unresolved answers remain')
    for doc in data['documents']:
        if digest(local_path(doc['path'], root)) != doc['sha256']:
            raise ValueError('Attachment changed; recreate the packet and request a new review')
    if digest(local_path(data['answers_file'], root)) != data['answers_sha256']:
        raise ValueError('Answers changed; recreate the packet and request a new review')
    if require_approval:
        approval = data.get('approval')
        if data.get('status') != 'approved' or not approval:
            raise ValueError('Explicit final user approval is required')
        unsigned = dict(data, status='awaiting_review', approval=None)
        if approval.get('review_sha256') != review_hash(unsigned):
            raise ValueError('Reviewed content changed; obtain fresh user approval')
    return data


def review_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def approve(root, packet, confirmation):
    if not confirmation.strip():
        raise ValueError('Record the actual explicit final user confirmation')
    data = check(root, packet)
    if data['status'] == 'approved':
        raise ValueError('Already approved; do not replay a submission')
    data['approval'] = {'user_confirmation': confirmation,
                        'review_sha256': review_hash(data),
                        'approved_at': datetime.now(timezone.utc).isoformat()}
    data['status'] = 'approved'
    atomic_json(packet_path(packet, root), data)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    for name in ('output', 'company', 'role', 'job-url', 'application-url', 'resume', 'answers'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--cover-letter')
    p = sub.add_parser('check')
    p.add_argument('--packet', required=True)
    p.add_argument('--require-approval', action='store_true')
    p = sub.add_parser('approve')
    p.add_argument('--packet', required=True)
    p.add_argument('--user-confirmation', required=True)
    args = ap.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(ROOT, args.output, args.company, args.role, args.job_url,
                             args.application_url, args.resume, args.cover_letter, args.answers)
        elif args.command == 'approve':
            result = approve(ROOT, args.packet, args.user_confirmation)
        else:
            result = check(ROOT, args.packet, args.require_approval)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'Not ready: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
