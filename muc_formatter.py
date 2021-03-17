#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 14:50:18 2021

@author: aaron
"""
import re
from bs4 import BeautifulSoup
import os
import json
import pandas as pd

from nltk import word_tokenize

def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    f.close()
    return data

def clean_text(text:str):
    text = text.strip().replace('  ', ' ').replace("``", "").replace("''", "").replace("---", "")
    return word_tokenize(text)

def convert_coref_keys(corefs):
    new_corefs = ['' if 'raw text' in obj.keys() else convert_coref_keys(obj['COREF']) if isinstance(obj['COREF'], list) else {'span': obj['COREF'], 'id': obj['tag_attrs']['ID'] if 'ID' in obj['tag_attrs'].keys() else 'no_id', 'ref': obj['tag_attrs']['REF'] if 'REF' in obj['tag_attrs'].keys() else 'no_ref'} for obj in corefs]
    new_corefs = [coref[0] if (isinstance(coref, list) and len(coref)==1) else coref for coref in new_corefs]
    new_corefs = [coref for coref in new_corefs if coref!='']
    return new_corefs


def extract_ner_coref(train_data:dict):
    no_match1 = []
    ner_dict = []
    # Parses through ner to form ner dict
    for key_dict, text_dict in zip(train_data['ner_keys'][0], train_data['ner_text'][0]):
        doc_id = text_dict['DOC'][0]['DOCID'].replace(' ', '').replace('.', '').replace('nyt', '')
        story_id = text_dict['DOC'][1]['STORYID'].strip().replace('.', '')
        date = text_dict['DOC'][3]['DATE'].strip().replace('.', '')
        text = clean_text(text_dict['DOC'][6]['TEXT'])
        
        if key_dict['DOC'][1]['STORYID'] == text_dict['DOC'][1]['STORYID']:
            entities = key_dict['DOC'][6]['TEXT']
            ner_dict.append({'doc_id': doc_id, 'story_id': story_id, 'date': date, 'text': text, 'entities': entities})
        else:        
            ner_dict.append({'doc_id': doc_id, 'story_id': story_id, 'date': date, 'text': text})
            no_match1.append({'doc_id': doc_id, 'story_id': story_id, 'date': date, 'text': text}) # Used to collect any unmatched samples
    
    coref_dict = [] 
    # get list of docs with coref keys
    coref_w_keys = [{'doc_id': keys['DOC'][0]['DOCID'], 'story_id': keys['DOC'][1]['STORYID'], 'date': keys['DOC'][3]['DATE'], 'coref': keys['DOC'][6]['TEXT']} for keys in train_data['coref_keys'][0]]
    
    # Parses through raw coref to form coref dict, if raw coref has coref keys - merge them
    for text_dict in train_data['coref_text'][0]:
        doc_id = text_dict['DOC'][0]['DOCID'].strip().replace('.', '').replace('nyt', '')
        story_id = text_dict['DOC'][1]['STORYID'].strip().replace('.', '')
        date = text_dict['DOC'][3]['DATE'].strip().replace('.', '')
        text = clean_text(text_dict['DOC'][6]['TEXT'])
     
        index_list = [text_dict['DOC'][0]['DOCID']==keys['doc_id'] for keys in coref_w_keys]
        if True in index_list:
            coref =  convert_coref_keys(coref_w_keys[index_list.index(True)]['coref'])
            coref_dict.append({'doc_id': doc_id, 'story_id': story_id, 'date': date, 'text': text, 'coref': coref})
        else:
            coref_dict.append({'doc_id': doc_id, 'story_id': story_id, 'date': date, 'text': text})

    return ner_dict, coref_dict

def extract_template_keys(key_data):
    df = pd.DataFrame.from_dict(key_data).transpose()
    df.reset_index(inplace=True)
    df = df.rename(columns = {'index':'keys'})
    
    # split the key string to get docid 
    new = df["keys"].str.split("-", n = 2, expand = True)
    # aggregate data by docid
    df['class'], df['docid'], df['part'] = new[new.columns[0]], new[new.columns[1]], new[new.columns[2]]
    groups = df.groupby('docid').agg({col:list for col in df.columns if col not in ['docid', 'class','part']}).to_dict(orient='index')
    
    # Convert to list of docid-dicts and filters non-nan entries
    new_data = []
    for docid in groups.keys():
        new_data.append({docid: [{key.lower(): groups[docid][key][idx] for key in groups[docid].keys() if groups[docid][key][idx]==groups[docid][key][idx]} for idx in range(len(groups[docid]['ENT_NAME']))]})
    
    return new_data

def format_dataset(train_data: dict):
    ner_dict, coref_dict = extract_ner_coref(train_data)
    # entities from each doc
    entities = extract_template_keys(train_data['template_elements'])
    # entity relations consist of multiple entities
    relations = extract_template_keys(train_data['template_relations'])
    # scenarios/events consist of multiple entity relations
    events = extract_template_keys(train_data['scenario_template'])
        
    for idx, ner_entities_relations_events in enumerate(zip(ner_dict, entities, relations, events)):    
        ner = ner_entities_relations_events[0]
        entities = ner_entities_relations_events[1]
        relations = ner_entities_relations_events[2]
        events = ner_entities_relations_events[3]
        index_list = [ner['doc_id']==keys['doc_id'] for keys in coref_dict]
        if True in index_list:
            ner_dict[idx]['coref'] = coref_dict[index_list.index(True)]['coref'] if 'coref' in coref_dict[index_list.index(True)].keys() else 'no_keys'
        ner_dict[idx]['entities'] = entities[ner['doc_id']]
        ner_dict[idx]['relations'] = relations[ner['doc_id']]
        ner_dict[idx]['events'] = events[ner['doc_id']]    
    return ner_dict

data = load_json('muc7.json')

# =============================================================================
data['training'] = format_dataset(data['training'])

# Have to sort out the duplicate keys issue for dryrun and formal in parsing
# data['dryrun'] = format_dataset(data['dryrun'])
# data['formaltst'] = format_dataset(data['formaltst'])
# =============================================================================








