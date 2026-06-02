#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path

ALIASES = [
    (('gearbox', 'gear box', 'reduction gearbox', '기어박스', '기어 박스', '감속기'), 'gearbox', 'Gearbox'),
    (('robot gripper', 'gripper', '그리퍼', '로봇 그리퍼'), 'robot_gripper', 'Robot gripper'),
    (('robot arm joint', 'robot arm', '로봇암', '로봇 암', '조인트', '관절'), 'robot_arm_joint', 'Robot arm joint'),
    (('linear actuator', 'actuator', '리니어 액추에이터', '액추에이터'), 'linear_actuator', 'Linear actuator'),
    (('drone frame', 'drone', '드론 프레임', '드론'), 'drone_frame', 'Drone frame'),
    (('landing gear', '랜딩기어', '랜딩 기어'), 'landing_gear', 'Landing gear'),
    (('camera mount', '카메라 마운트', '마운트'), 'camera_mount', 'Camera mount'),
    (('watch escapement', 'watch mechanism', 'escapement', '시계', '탈진기', '이스케이프먼트'), 'watch_escapement', 'Watch escapement'),
    (('cnc fixture', 'fixture', 'workholding', '지그', '픽스처', '치공구'), 'cnc_fixture', 'CNC fixture'),
    (('enclosure', 'housing', 'case', '인클로저', '하우징', '케이스'), 'enclosure', 'Enclosure'),
    (('bracket', '브라켓', '브래킷'), 'bracket', 'Bracket'),
]

STOPWORDS = {
    'a', 'an', 'and', 'cad', 'create', 'design', 'for', 'i', 'make', 'me', 'model', 'please',
    'start', 'the', 'to', 'want', 'with', 'would', 'like', 'build', 'need', 'new', 'project',
}


def compact(text: str) -> str:
    return re.sub(r'\s+', '', text.casefold())


def alias_for_request(request: str) -> tuple[str, str] | None:
    lowered = request.casefold()
    compacted = compact(request)
    for terms, slug, title in ALIASES:
        for term in terms:
            if term.casefold() in lowered or compact(term) in compacted:
                return slug, title
    return None


def slugify(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    words = re.findall(r'[a-zA-Z0-9]+', normalized.casefold())
    filtered = [word for word in words if word not in STOPWORDS]
    slug = '_'.join(filtered[:6]).strip('_')
    return slug or 'cad_job'


def title_from_slug(slug: str) -> str:
    base = re.sub(r'^\d{3}_', '', slug).replace('_', ' ').strip()
    return base[:1].upper() + base[1:] if base else 'CAD job'


def derive_slug_title(request: str) -> tuple[str, str]:
    cleaned = ' '.join(request.strip().split())
    if not cleaned:
        raise SystemExit('ERROR: empty milestone request')
    alias = alias_for_request(cleaned)
    if alias is not None:
        return alias
    slug = slugify(cleaned)
    if slug == 'cad_job':
        return slug, cleaned
    return slug, title_from_slug(slug)


def next_milestone_id(root: Path, slug: str) -> str:
    milestones_dir = root / 'milestones'
    used = []
    if milestones_dir.exists():
        for child in milestones_dir.iterdir():
            if child.is_dir():
                match = re.match(r'^(\d{3})_', child.name)
                if match:
                    used.append(int(match.group(1)))
    next_number = max(used, default=0) + 1
    return f'{next_number:03d}_{slug}'


def create_milestone(root: Path, milestone_id: str, title: str, maturity: str) -> Path:
    template = root / 'milestones/_template'
    milestones_dir = (root / 'milestones').resolve()
    target = (milestones_dir / milestone_id).resolve()
    if target.parent != milestones_dir:
        raise SystemExit('ERROR: milestone id must name a direct child under milestones/')
    if target.exists():
        raise SystemExit(f'ERROR: milestone already exists: {target}')
    shutil.copytree(template, target)
    replacements = {
        'REPLACE_WITH_MILESTONE_ID': milestone_id,
        'REPLACE_WITH_TITLE': title,
        'REPLACE_WITH_DATE': date.today().isoformat(),
        'REPLACE_WITH_MATURITY': maturity,
        '"maturity": "concept"': f'"maturity": "{maturity}"',
    }
    for path in target.rglob('*'):
        if not path.is_file() or path.suffix not in {'.md', '.yaml', '.json', '.csv'}:
            continue
        text = path.read_text(encoding='utf-8')
        for needle, replacement in replacements.items():
            text = text.replace(needle, replacement)
        path.write_text(text, encoding='utf-8')
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description='Create a Zen CAD milestone from explicit id/title or a natural-language CAD request.')
    parser.add_argument('request_words', nargs='*', help='Natural-language CAD request, e.g. "기어 박스를 만들고 싶어"')
    parser.add_argument('--request', help='Natural-language CAD request. The script derives the next milestone id and title.')
    parser.add_argument('--id', help='Explicit milestone id, e.g. 002_gearbox')
    parser.add_argument('--title', help='Explicit human-readable milestone title')
    parser.add_argument('--root', default='.', help='Zen CAD repository root')
    parser.add_argument('--maturity', choices=['concept', 'layout', 'final'], default='concept', help='Initial milestone maturity. Defaults to concept so agents can generate before final evidence gates.')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    request = args.request or ' '.join(args.request_words)

    if args.id and args.title:
        milestone_id = args.id
        title = args.title
    elif args.id and request:
        milestone_id = args.id
        _, title = derive_slug_title(request)
    elif args.title and not args.id:
        slug, title = derive_slug_title(args.title)
        milestone_id = next_milestone_id(root, slug)
    elif request:
        slug, title = derive_slug_title(request)
        milestone_id = next_milestone_id(root, slug)
    else:
        raise SystemExit('ERROR: provide --id and --title, or provide a natural-language request with --request "..."')

    target = create_milestone(root, milestone_id, title, args.maturity)
    print(f'Created milestone: {target}')
    print(f'Milestone id: {milestone_id}')
    print(f'Title: {title}')
    print(f'Maturity: {args.maturity}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
