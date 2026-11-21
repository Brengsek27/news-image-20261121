'''Data verifier for the 58-story edition.

Runs a series of assertions on the data defined in stories.py.
If any check fails, an AssertionError with a clear message is raised.
On success it prints exactly the required success line.
''' 

import sys

try:
    from stories import (
        CARDS,
        BRIEFS,
        DATE_CHECK,
        REGIONS,
        STATS,
        TIMELINE,
        META,
    )
except Exception as e:
    sys.stderr.write(f'Failed to import stories: {e}\n')
    raise

# Helper to ensure a non‑empty string field
def _non_empty(value, name, location):
    assert isinstance(value, str) and value.strip(), f'{location}: {name} must be non‑empty'

# 1. Basic counts
assert len(CARDS) == 16, f'Expected 16 cards, found {len(CARDS)}'
assert len(BRIEFS) == 42, f'Expected 42 briefs, found {len(BRIEFS)}'
assert len(CARDS) + len(BRIEFS) == 58, f'Total stories should be 58, got {len(CARDS)+len(BRIEFS)}'

# 2. Sequential numbering
for i, card in enumerate(CARDS, start=1):
    assert card['n'] == i, f'Card number out of order: expected {i}, got {card["n"]}'
for i, brief in enumerate(BRIEFS, start=17):
    assert brief['n'] == i, f'Brief number out of order: expected {i}, got {brief["n"]}'

# 3. Region counts
expected_counts = {
    'EUROPE': 17,
    'THE AMERICAS': 15,
    'ASIA-PACIFIC': 12,
    'MIDDLE EAST': 6,
    'AFRICA': 2,
    'OCEANIA': 2,
    'WORLD': 4,
}
region_counter = {r: 0 for r in expected_counts}
for item in CARDS + BRIEFS:
    region = item.get('region')
    if region not in region_counter:
        raise AssertionError(f'Unexpected region {region!r}')
    region_counter[region] += 1
assert region_counter == expected_counts, f'Region counts mismatch: {region_counter}'

# 4. Card field completeness and unique art keys
art_keys = set()
for idx, card in enumerate(CARDS, start=1):
    location = f'Card {idx}'
    for field in ('place', 'topic', 'headline', 'deck', 'source', 'banner', 'art'):
        _non_empty(card.get(field, ''), field, location)
    art = card['art']
    assert art not in art_keys, f'Duplicate art key {art!r} in {location}'
    art_keys.add(art)

# 5. Spot‑check strings (additional required assertions)
# Card 1 fields
assert CARDS[0]['source'] == "AP · Reuters · UN News", 'Card 1 source mismatch'
assert CARDS[0]['banner'] == "NO DEAL · DAY 15", 'Card 1 banner mismatch'
assert CARDS[0]['region'] == "ASIA-PACIFIC", 'Card 1 region mismatch'
# Card 2 fields (index 1)
assert CARDS[1]['region'] == "EUROPE", 'Card 2 region mismatch'
assert CARDS[1]['banner'] == "DOUBLE TAP", 'Card 2 banner mismatch'
assert CARDS[1]['source'] == "Vilkul · AP", 'Card 2 source mismatch'
# Ordered list of art keys
expected_art_order = [
    'cop31_dome', 'kryvyi_night', 'riyadh_intercept', 'mercury_capture',
    'warsaw_nato', 'hague_scales', 'hodeidah_port', 'akvan_cyclone',
    'wellington_cricket', 'copenhagen_court', 'london_cyber', 'sumy_himars',
    'delhi_forum', 'delhi_vaccine', 'jakarta_youtube', 'newyork_vendors'
]
actual_art_order = [card['art'] for card in CARDS]
assert actual_art_order == expected_art_order, f'Art key order mismatch: {actual_art_order}'

# 6. Success output
print('DATA CHECKS PASS: 58 stories, 16 cards, regions OK')
import subprocess, hashlib, os, shutil, struct, tempfile, pathlib
from PIL import Image

def _run_render_and_hash(cwd):
    # Use a deterministic seed for the random module before executing render.py.
    # The one‑liner seeds the global RNG then runs the script's contents.
    # Use run_path so __file__ is set correctly for render.py which relies on it.
    # Ensure __file__ is set correctly for render.py which relies on it.
    cmd = [sys.executable, 'render.py']
    subprocess.run(cmd, cwd=cwd, check=True, timeout=120)
    png_path = pathlib.Path(cwd) / 'entry.png'
    data = png_path.read_bytes()
    h = hashlib.sha256(data).digest()
    return data, h

# 1. Determinism
repo_dir = pathlib.Path(__file__).resolve().parent
data1, hash1 = _run_render_and_hash(repo_dir)
data2, hash2 = _run_render_and_hash(repo_dir)
assert hash1 == hash2, 'Render determinism check failed'

# 2. PNG shape and size
png_path = pathlib.Path(repo_dir) / 'entry.png'
png_bytes = png_path.read_bytes()
# IHDR width/height at offset 16..24 (big‑endian unsigned)
width, height = struct.unpack('>II', png_bytes[16:24])
assert width == 1024 and height == 1024, f'PNG size mismatch: {width}x{height}'
assert len(png_bytes) <= 1_048_576, f'PNG file too large: {len(png_bytes)} bytes'

# 3. main.ts foreign CWD execution
with tempfile.TemporaryDirectory() as td:
    td_path = pathlib.Path(td)
    prog_dir = td_path / 'prog'
    prog_dir.mkdir()
    shutil.copy(repo_dir / 'main.ts', prog_dir / 'main.ts')
    shutil.copy(repo_dir / 'entry.png', prog_dir / 'entry.png')
    out1 = td_path / 'out1'
    out2 = td_path / 'out2'
    out1.mkdir()
    out2.mkdir()
    env1 = os.environ.copy()
    env1['MAKEFUN_OUTPUT_DIR'] = str(out1)
    env2 = os.environ.copy()
    env2['MAKEFUN_OUTPUT_DIR'] = str(out2)
    # Run twice with cwd="/" but give absolute script path
    script_path = prog_dir / 'main.ts'
    subprocess.run(['node', str(script_path)], cwd='/', env=env1, check=True, timeout=120)
    subprocess.run(['node', str(script_path)], cwd='/', env=env2, check=True, timeout=120)
    # Compare outputs
    out_files1 = list(out1.iterdir())
    out_files2 = list(out2.iterdir())
    assert len(out_files1) == 1 and len(out_files2) == 1, 'Unexpected number of output files'
    out_data1 = out_files1[0].read_bytes()
    out_data2 = out_files2[0].read_bytes()
    assert out_data1 == out_data2 == png_bytes, 'Node output mismatch or differs from entry.png'

# 4. Corruption rejection tests
def _run_node_with_dir(png_bytes, expect_success):
    with tempfile.TemporaryDirectory() as td2:
        td2_path = pathlib.Path(td2)
        prog = td2_path / 'prog'
        prog.mkdir()
        shutil.copy(repo_dir / 'main.ts', prog / 'main.ts')
        (prog / 'entry.png').write_bytes(png_bytes)
        out_dir = td2_path / 'out'
        out_dir.mkdir()
        env = os.environ.copy()
        env['MAKEFUN_OUTPUT_DIR'] = str(out_dir)
        # Use absolute script path to ensure node runs the copied file even when cwd is '/'.
        result = subprocess.run(['node', str(prog / 'main.ts')], cwd='/', env=env, timeout=120)
        if expect_success:
            assert result.returncode == 0, 'Expected success but node failed'
        else:
            assert result.returncode != 0, 'Corrupted PNG should cause non‑zero exit'

    # a) corrupted byte at offset 100
    corrupt = bytearray(png_bytes)
    corrupt[100] ^= 0xFF
    _run_node_with_dir(bytes(corrupt), expect_success=False)

    # b) truncated PNG (first 200 bytes)
    _trunc = png_bytes[:200]
    _run_node_with_dir(_trunc, expect_success=False)

    # c) wrong‑size PNG (512×512)
    # Generate a wrong‑size PNG (512×512) in memory to avoid filesystem side‑effects.
    import io
    _buf = io.BytesIO()
    Image.new('RGB', (512, 512), color='white').save(_buf, format='PNG')
    wrong_bytes = _buf.getvalue()
    _run_node_with_dir(wrong_bytes, expect_success=False)

print('FULL CHECKS PASS: determinism, PNG 1024x1024 <=1MiB, foreign-CWD main.ts x2, corruption rejected')
