"""Synthetic source-order checks for astro schema 1.3 (developer tests only).

These are never part of the normal single-paper reading workflow.
"""
import copy
import json
import subprocess
import sys

import pytest

from astro_xray.report import ROOT, render_markdown, render_notes, validate_analysis


@pytest.fixture
def original_order(ready):
    data = copy.deepcopy(ready)
    data['schema_version'] = '1.3'
    data['paper']['kind'] = 'observation'
    data['reader'] = dict(
        overview='A synthetic research-reading fixture, not a real observation.',
        argument_route='§1 poses the question; §2 explains data and method; §3 analyzes a result; §4 sets its scope.',
        organization='paper-order',
        roadmap=[dict(section=label, title=title, argument=goal,
                      focus='Synthetic source excerpt', source_id='local', page=i)
                 for i, (label, title, goal) in enumerate([
                    ('§1', 'Question', 'Why study this problem'),
                    ('§2', 'Observations', 'How the data are used'),
                    ('§3', 'Results', 'What is found'),
                    ('§4', 'Conclusions', 'Interpretation and scope'),
                ], start=1)],
        focus=[])
    for sec, labels in zip(data['sections'], [['§1'], ['§2'], ['§2'], ['§3'], ['§4'], []]):
        sec['source_sections'] = labels
    return data


def test_original_route_precedes_body_and_map_follows(original_order):
    validate_analysis(original_order, publish=True)
    md = render_markdown(original_order)
    assert md.index('## 论文论证路线') < md.index('## background')
    assert md.index('## 原文结构导览') > md.index('## review')
    assert '§1' in md and '§4' in md
    notes = render_notes(original_order)
    assert 'paper-order' in notes and '- method: §2' in notes


@pytest.mark.parametrize('bad,part', [
    ('missing-mapping','source_sections'),
    ('wrong-original-label','Unknown original-paper chapter'),
    ('missing-original-chapter','all be covered'),
    ('reversed-original-order','chapter order'),
    ('independent-commentary-first','Independent commentary'),
    ('non-review-unmapped','clearly separate review'),
    ('missing-route','argument route'),
    ('missing-organization','organization'),
])
def test_invalid_source_mapping_rejected(original_order, bad, part):
    data=copy.deepcopy(original_order)
    sections=data['sections']
    if bad == 'missing-mapping':
        del sections[0]['source_sections']
    elif bad == 'wrong-original-label':
        sections[0]['source_sections']=['§999']
    elif bad == 'missing-original-chapter':
        sections[4]['source_sections']=['§3']
    elif bad == 'reversed-original-order':
        sections[1]['source_sections'],sections[3]['source_sections']=sections[3]['source_sections'],sections[1]['source_sections']
    elif bad == 'independent-commentary-first':
        sections[0]['source_sections']=[]
        sections[0]['role']='review'
    elif bad == 'non-review-unmapped':
        sections[0]['source_sections']=[]
    elif bad == 'missing-route':
        data['reader']['argument_route']=''
    else:
        del data['reader']['organization']
    with pytest.raises(ValueError,match=part):
        validate_analysis(data,publish=True)


def test_restructuring_requires_concrete_reason(original_order):
    data=copy.deepcopy(original_order)
    data['sections'][1]['source_sections']=['§3']
    data['sections'][3]['source_sections']=['§2']
    data['reader']['organization']='restructured'
    with pytest.raises(ValueError,match='explain a concrete departure'):
        validate_analysis(data,publish=True)
    data['reader']['departure_reason']='Explicit request: thematic comparison of results and observations.'
    validate_analysis(data,publish=True)


def test_does_not_require_duplicate_internal_plans(original_order):
    assert 'throughline' not in original_order['reader']
    assert 'connections' not in original_order['reader']
    original_order['unknowns']=[]
    validate_analysis(original_order,publish=True)
    assert '论文论证路线' in render_markdown(original_order)


def test_theory_does_not_need_a_fictitious_experiment(original_order):
    data=copy.deepcopy(original_order)
    data['paper']['kind']='theory'
    data['sections']=[
        dict(id='definitions',role='background',title='§1 Definitions',markdown='Synthetic mathematical definitions.',claim_ids=['analytic'],source_sections=['§1','§2']),
        dict(id='proof',role='derivation',title='§3 Proof',markdown='A synthetic derivation.',claim_ids=['analytic'],source_sections=['§3']),
        dict(id='conclusion',role='limitations',title='§4 Scope',markdown='Scope of the theorem.',claim_ids=['analytic'],source_sections=['§4'])]
    validate_analysis(data,publish=True)


def test_quick_partial_does_not_claim_full_coverage(original_order):
    data=copy.deepcopy(original_order)
    data['mode']='quick'
    data['coverage'].update(level='abstract',teaching_only=False)
    data['reader'].update(roadmap=[],argument_route='')
    for sec in data['sections']:
        sec.pop('source_sections',None)
    validate_analysis(data,publish=True)


def test_new_draft_has_source_order_defaults(tmp_path):
    result=subprocess.run([sys.executable,str(ROOT/'scripts/new_analysis.py'),'local-paper.pdf',
                           '--out',str(tmp_path)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    data=json.loads((tmp_path/'analysis.json').read_text(encoding='utf-8'))
    assert data['schema_version']=='1.3'
    assert data['reader']['organization']=='paper-order'
    assert data['reader']['argument_route']==''
    validate_analysis(data)
    with pytest.raises(ValueError):
        validate_analysis(data,publish=True)


def test_legacy_example_remains_valid():
    data=json.loads((ROOT/'examples/ogle-2016-blg-1928/analysis.json').read_text(encoding='utf-8'))
    validate_analysis(data,publish=True)
