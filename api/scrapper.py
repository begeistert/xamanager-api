import requests
import mistletoe
from models import Version
from mistletoe.markdown_renderer import MarkdownRenderer, LinkReferenceDefinitionBlock, LinkReferenceDefinition
from mistletoe.block_token import Table
import mistletoe.span_token as span_tokens


def get_document_from_url(url: str):
    reqs = requests.get(url)
    content = reqs.content.decode('utf-8')
    with MarkdownRenderer(max_line_length=1):
        doc = mistletoe.Document(content)

    return doc


def scrape_links(markdown, first_in_table=False, expand_url=True):
    def process_link(link_node: LinkReferenceDefinition):
        if not str(link_node.dest).endswith('macos'):
            return
        if 'aka.ms' in str(link_node.dest):
            if expand_url:
                session = requests.Session()
                resp = session.head(link_node.dest, allow_redirects=True)
                if resp.status_code == 200:
                    versions.append(_process_version_from_url(resp.url, short_url=link_node.dest))
            else:
                versions.append(_process_version_from_url('', short_url=link_node.dest, expanded_url=False))
        else:
            versions.append(_process_version_from_url(link_node.dest))

    def process_span_link(span_node: span_tokens.Link):
        target = span_node.target
        if 'xamarin.' not in target:
            return
        if 'aka.ms' in str(target):
            session = requests.Session()
            resp = session.head(target, allow_redirects=True)
            if resp.status_code == 200:
                versions.append(_process_version_from_url(resp.url, short_url=target))
        else:
            versions.append(_process_version_from_url(target))

    versions = []
    doc = markdown.children
    for node in doc:
        first_found = False
        if isinstance(node, LinkReferenceDefinitionBlock):
            for link in node.children:
                process_link(link)
        if isinstance(node, Table):
            for row in node.children:
                for cell in row.children:
                    for child in cell.children:
                        if isinstance(child, span_tokens.Link):
                            process_span_link(child)
                            if first_in_table:
                                first_found = True
                                break
                        if first_found and first_in_table:
                            break
                    if first_found and first_in_table:
                        break
                if first_found and first_in_table:
                    break

    return versions


def _process_version_from_url(url, short_url=None, expanded_url=True) -> Version:
    if expanded_url:
        platform = url.split('/')[-1].split('-')[0].split('.')[-1]
        version = url.split('/')[-1].replace('.pkg', '').replace(f'xamarin.{platform}-', '')
        if '-' in version:
            version = version.replace('-', '.')
        if '?' in version:
            version = version.split('?')[0]
        if 'monotouch' in version:
            version = version.replace('monotouch.', '')
            platform = 'ios'
    else:
        platform = None
        version = None
    return Version(platform, version, url, short_url)


