import re
import yaml
from pathlib import Path
from typing import Tuple
import uuid

from typer import Typer
from rich import print

app = Typer()

vault_path = Path('~/writing/obsidian/main').expanduser()

def parse_file(path: Path) -> Tuple[str, str]:
    with path.open() as f:
        frontmatter = ""
        frontmatter_mode = False
        text = ""
        lines = f.readlines()
        if len(lines) == 0:
            return None, ""
        if lines[0].startswith('---'):
            lines = lines[1:]
            frontmatter_mode = True
        for line in lines:
            if line.startswith('---'):
                frontmatter_mode = False
                continue
            if frontmatter_mode:
                frontmatter += line
            else:
                text += line
    if frontmatter in ["", None]:
        frontmatter = None
    else:
        frontmatter = yaml.load(frontmatter, Loader=yaml.FullLoader)

    return frontmatter, text

@app.command()
def validate_references():
    for f in Path(f'{vault_path}/references').iterdir():
        frontmatter, text = parse_file(f)
        if not frontmatter or 'page-title' not in frontmatter or 'url' not in frontmatter:
            print(f"Invalid frontmatter in {f}:")
            print(frontmatter)

@app.command()
def validate_files():
    validate_references()
    for f in iterate_vault():
        frontmatter, text = parse_file(f)
        assert frontmatter is not None, f"Invalid frontmatter in {f}"
        assert 'id' in frontmatter
        assert 'permalink' in frontmatter
        assert frontmatter['id'] == frontmatter['permalink'], f"ID and permalink do not match in {f}"

def get_first_url(frontmatter):
    for key, url in frontmatter.items():
        if re.match(r'url.*', key):
            return url
    else:
        raise Exception(f"Could not select a url in frontmatter of {f}")

@app.command()
def extract_frontmatter_urls():
    for f in Path(f'{vault_path}/references').iterdir():
        frontmatter, text = parse_file(f)
        next_outer_itter = False
        for line in text.split('\n'):
            if "#python_obsidian/url_extraction" in line:
                print(f"Already found data therefore skipping: {line}")
                next_outer_itter = True
                break
        if next_outer_itter:
            continue
        first_url = get_first_url(frontmatter)
        name = None
        if 'page-title' in frontmatter:
            name = frontmatter['page-title']
        else:
            name = f.name
        content = (
            f'---\n'
            f'{yaml.dump(frontmatter)}\n'
            f'---\n'
            f'#python_obsidian/url_extraction [{name}]({first_url})\n'
            f'\n'
            f'{text}')
        f.open('w').write(content)

def iterate_vault():
    for f in Path(f'{vault_path}').rglob('*'):
        if not f.is_file() or f.suffix != '.md' or f.name.upper() == 'README.md' \
            or f.name == 'index.md' or '.obsidian' in str(f) or f.name.endswith('.excalidraw.md'):
            continue
        yield f

@app.command()
def list_vault_files():
    """List all files in the vault."""
    for f in iterate_vault():
        print(f)

@app.command()
def list_publish_tagged():
    """
    List all files that are tagged with `publish: true` in their frontmatter.
    """
    for f in iterate_vault():
        frontmatter, text = parse_file(f)
        if frontmatter and 'publish' in frontmatter and frontmatter['publish'] == 'true':
            print(f)

@app.command()
def add_permalinks():
    """
    Add permalink and id fields to all files that do not have them yet.
    """
    for f in iterate_vault():
        frontmatter, text = parse_file(f)
        if frontmatter and 'permalink' in frontmatter and 'id' in frontmatter:
            continue
        if frontmatter and 'id' in frontmatter:
            frontmatter['permalink'] = frontmatter["id"]
        elif frontmatter and 'permalink' in frontmatter:
            frontmatter['id'] = frontmatter["permalink"]
        else:
            id = uuid.uuid4()
            if frontmatter is None:
                frontmatter = {}
            frontmatter['id'] = str(id)
            frontmatter['permalink'] = str(id)
        f.open('w').write(
            f'---\n'
            f'{yaml.dump(frontmatter)}\n'
            f'---\n'
            f'{text}')

if __name__ == "__main__":
    app()