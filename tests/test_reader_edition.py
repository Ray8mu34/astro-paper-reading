import copy
import json

import pytest
from bs4 import BeautifulSoup
from astro_xray.report import ROOT, build_html, read_json, render_markdown, render_notes, validate_analysis
from test_pipeline import run


@pytest.fixture
def edition(ready):
    ready['schema_version'] = '1.1'
    ready['reader'] = dict(overview='Specific research question, difficulty, contribution, result and physical scope.',
        roadmap=[dict(section='§1', title='Original section', argument='Motivation', focus='Figure 1', source_id='local', page=2)],
        focus=[dict(section_id='method', question='Why this mechanism?', why='It resolves the central difficulty.')])
    ready['sources'][0]['url'] = 'https://example.org/paper.pdf'
    ready['sources'][0]['note'] = 'PRIVATE_ACCESS_LOG'
    ready['coverage']['read'] = ['PRIVATE_COVERAGE_LOG']
    ready['reproduction']['notes'] = ['PRIVATE_RUNTIME_LOG']
    ready['sections'].append(dict(id='private', role='review', title='PRIVATE_SECTION', markdown='PRIVATE_TOOL_LOG', claim_ids=[], audience='internal'))
    return ready


def test_reader_and_notes_are_distinct_artifacts(edition, tmp_path):
    path = tmp_path/'analysis.json'
    path.write_text(json.dumps(edition), encoding='utf-8')
    assert run('build_report.py', '--analysis', path).returncode == 0
    md = (tmp_path/'report.md').read_text(encoding='utf-8')
    notes = (tmp_path/'analysis-notes.md').read_text(encoding='utf-8')
    for marker in ['PRIVATE_ACCESS_LOG', 'PRIVATE_COVERAGE_LOG', 'PRIVATE_RUNTIME_LOG', 'PRIVATE_TOOL_LOG']:
        assert marker not in md
        assert marker in notes
    assert edition['reader']['overview'] in md
    assert 'Static point-mass lens' not in md  # no automatic assumptions dump
    page = BeautifulSoup((tmp_path/'report.html').read_text(encoding='utf-8'), 'html.parser')
    assert page.find('a', href='https://example.org/paper.pdf#page=2')
    assert page.find('a', href='#section-method') and page.find(id='section-method')
    assert run('validate_skill.py', '--analysis', path, '--require-artifacts').returncode == 0
    (tmp_path/'analysis-notes.md').write_text('lost evidence ledger', encoding='utf-8')
    assert run('validate_skill.py', '--analysis', path, '--require-artifacts').returncode != 0


def test_reader_planning_references_and_audiences(edition):
    invalid = copy.deepcopy(edition)
    del invalid['reader']
    with pytest.raises(ValueError, match='overview'):
        validate_analysis(invalid, publish=True)
    invalid = copy.deepcopy(edition)
    invalid['reader']['focus'][0]['section_id'] = 'private'
    with pytest.raises(ValueError, match='main reader'):
        validate_analysis(invalid, publish=True)
    invalid = copy.deepcopy(edition)
    invalid['reader']['roadmap'][0]['source_id'] = 'missing'
    with pytest.raises(ValueError, match='original source'):
        validate_analysis(invalid, publish=True)


def test_zero_visual_and_omitted_missing_assets_are_valid(edition):
    edition['mode'] = 'interactive-html'
    edition['visuals'] = [dict(id='unneeded', kind='image', section_id='method', placement='omit', question='Would this help?',
        why='Text suffices.', alternative='One sentence', caption='', basis='schematic', image='absent.png')]
    validate_analysis(edition, publish=True)
    page = BeautifulSoup(build_html(render_markdown(edition), analysis=edition), 'html.parser')
    assert not page.find('svg') and not page.find('img')
    assert 'Text suffices.' in render_notes(edition)


def test_abstract_quick_does_not_invent_original_sections(edition):
    edition['mode']='quick'
    edition['coverage'].update(level='abstract',teaching_only=False)
    edition['reader']['overview']='根据摘要，这项工作研究一个具体问题；完整论证留待阅读全文。'
    edition['reader']['roadmap']=[]
    validate_analysis(edition,publish=True)
    page=BeautifulSoup(build_html(render_markdown(edition),analysis=edition),'html.parser')
    assert not page.find('a',href='https://example.org/paper.pdf#page=2')
    edition['mode']='deep-md'
    with pytest.raises(ValueError):
        validate_analysis(edition,publish=True)


def test_supplement_does_not_hide_core_mechanism(edition):
    edition['sections'][4]['audience'] = 'appendix'
    edition['sections'][5]['audience'] = 'appendix'
    page = BeautifulSoup(build_html(render_markdown(edition), analysis=edition), 'html.parser')
    assert page.find(id='section-derivation').find_parent('details') is None
    assert page.find(id='section-limitations').find_parent('details')['class']==['supplement']
    assert page.select_one('details.reading-nav').get('open') is None


def test_manifest_assets_are_rebuilt_and_changes_rejected(edition, tmp_path):
    import base64
    data = copy.deepcopy(edition)
    data['mode'] = 'interactive-html'
    (tmp_path/'sources').mkdir()
    (tmp_path/'visuals').mkdir()
    png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jB1kAAAAASUVORK5CYII=')
    data['visuals'] = []
    for number in range(1, 5):
        image = f'sources/figure-{number}.png'
        (tmp_path/image).write_bytes(png)
        data['visuals'].append(dict(id=f'image-{number}',kind='image',section_id='method',placement='include',
            question='What evidence matters?',why='Inspect a synthetic fixture.',alternative='Text',
            caption='Synthetic test image',basis='schematic',image=image))
    (tmp_path/'visuals/module.html').write_text('<section class="experiment" id="fixture-experiment">Synthetic mechanism</section>', encoding='utf-8')
    (tmp_path/'visuals/module.js').write_text('window.fixtureLoaded = true;', encoding='utf-8')
    data['visuals'].append(dict(id='mechanism',kind='interactive',section_id='method',placement='include',
        question='How does a change affect the mechanism?',why='Compare a counterfactual.',alternative='Static diagram',
        caption='Synthetic test mechanism',basis='schematic',interaction_gain='Expose the counterfactual',
        fragment='visuals/module.html',script='visuals/module.js'))
    data['visuals'].append(dict(id='unneeded',kind='image',section_id='method',placement='omit',
        question='Does this help?',why='Text suffices.',alternative='One sentence',caption='',basis='schematic',image='missing.png'))
    data['sections'][1]['markdown'] += '\n\n' + '\n\n'.join(
        f'<!-- astro-visual:{visual["id"]} -->' for visual in data['visuals'] if visual['placement']=='include')
    path=tmp_path/'analysis.json'
    path.write_text(json.dumps(data, ensure_ascii=False),encoding='utf-8')
    assert run('build_report.py','--analysis',path).returncode==0
    assert run('validate_skill.py','--analysis',path,'--require-artifacts').returncode==0
    page=BeautifulSoup((tmp_path/'report.html').read_text(encoding='utf-8'),'html.parser')
    assert len(page.find_all('img'))==4 and len(page.select('.experiment'))==1
    assert page.find(id='fixture-experiment') and not page.find(id='visual-unneeded')
    for img in page.find_all('img'):
        assert img['src'].startswith('data:image/png;base64,')
    original=(tmp_path/'report.html').read_bytes()
    asset=tmp_path/'visuals/module.js'
    asset.write_text(asset.read_text(encoding='utf-8')+'\n// changed asset',encoding='utf-8')
    assert run('validate_skill.py','--analysis',path,'--require-artifacts').returncode!=0
    (tmp_path/'sources/figure-4.png').unlink()
    assert run('build_report.py','--analysis',path).returncode!=0
    assert (tmp_path/'report.html').read_bytes()==original


def test_visual_without_teaching_reason_or_invalid_path_rejected(edition):
    edition['visuals']=[dict(id='interactive',kind='interactive',section_id='method',placement='include',question='Why?',
        why='Benefit',alternative='Static',caption='Conditional model',basis='analytic',fragment='module.html')]
    with pytest.raises(ValueError,match='interaction gain'):
        validate_analysis(edition,publish=True)
    edition['visuals'][0]['interaction_gain']='A physical counterfactual'
    edition['visuals'][0]['fragment']='../outside.html'
    with pytest.raises(ValueError,match='escapes workspace'):
        validate_analysis(edition,publish=True)
