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

def load_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        string = f.read()
    f.close()
    return string

def quotations(matchobj):
    string = matchobj.group(0)
    string = string.replace('=', '="')+'"'
    return string
    
def angle_brackets(matchobj):
    string = matchobj.group(0)
    string = string.replace('<','').replace('>','')
    #string_list = string.split()       
    tag = string.split()[0]
    para_list = [group[0] for group in re.findall(r'([\w]+[/=][/"]?([\w]+[\W]?)+[/"]?[\s\>])', string)]
    string_list = [tag]+para_list
    string_list = [re.sub('(=[\w\s\']+)', quotations, element) if idx!=0 and '"' not in element and '/' not in element else element for idx, element in enumerate(string_list)]
    #print('<'+' '.join(string_list)+'>')
    return '<'+' '.join(string_list)+'>'

def extract_children(tag):
    children = tag.findChildren(recursive=False)
    if len(children)!=0:     
        if tag.name=='TEXT':
            text = [{'raw text': tag.text}]
            return [{child.name: extract_children(child), 'tag_attrs': child.attrs} for child in children if child!=None]+text
        else:
            return [{child.name: extract_children(child), 'tag_attrs': child.attrs} for child in children if child!=None]
    else:
        return tag.text

def process_keys(sample):

    def clean_text(text):
        return text.replace('/', '').strip().replace('"', '').replace('<', '').replace('>', '')
    
    dataset = {}
    for line in sample.split('\n'):
        if re.match('<[\S]+> :=', line):
            key = line.replace(' :=', '').replace('<', '').replace('>', '')
            key_value = ''
            dataset[key] = {}
        elif ': ' not in line and '/' in line and key_value!='': 
            dataset[key][key_value[0]] = dataset[key][key_value[0]]+[clean_text(line)]
        else:
            if ': ' in line:
                key_value = line.strip().split(':')
            if key_value!='' and len(key_value)>1:
                dataset[key].update({key_value[0]: [clean_text(key_value[1])]})
            else:
                print('ERROR:')
                print(line)
                print(key_value)
    return dataset

def convert_keys(input_dict):
    new_data = {}
    for key in input_dict.keys():
        if '.co.keys' in key:
            new_data['coref_keys'] = input_dict[key]
        elif '.co.texts' in key:
            new_data['coref_text'] = input_dict[key]
        elif ('ne' in key or 'ie' in key) and 'text' in key:
            new_data['ner_text'] = input_dict[key]
        elif 'ne.eng.keys' in key:
            new_data['ner_keys'] = input_dict[key]
        elif 'st.keys' in key:
            new_data['scenario_template'] = input_dict[key]
        elif 'te.keys' in key:
            new_data['template_elements'] = input_dict[key]
        elif 'tr.keys' in key:
            new_data['template_relations'] = input_dict[key]
        else:
            print('error:', key)
    return new_data

def run_muc_parser(data_dir:str):
    dataset = {'dryrun': {}, 'formaltst': {}, 'training': {}}
    
    for root, dirs, files in os.walk(data_dir, topdown=False):
        for name in files:
            if name != 'README':
                file_path = os.path.join(root, name)
                print('Reading {}'.format(file_path))            
    
                if 'st.keys' in file_path or 'te.keys' in file_path or 'tr.keys' in file_path:
                    sample = load_file(file_path)
                    sample = re.sub('<(.+?)>', angle_brackets, sample)                         
                    doc = process_keys(sample)            
                else:
                    sample = load_file(file_path).replace('\n','').replace('<p>', '') #.replace(',', '')
                    sample = re.sub('<(.+?)>', angle_brackets, sample)                         
        
                    soup = BeautifulSoup('<html>'+sample+'</html>', 'lxml-xml')
                    doc = [extract_children(tag) for tag in soup.find_all(recursive=False)]
    
                if 'dryrun' in name:
                    #dataset['dryrun'].update(convert_keys({name: doc}))
                    dataset['dryrun'].update({name: doc})

                elif 'formal' in name:
                    #dataset['formaltst'].update(convert_keys({name: doc}))
                    dataset['formaltst'].update({name: doc})
                
                elif 'training' in name:
                    dataset['training'].update(convert_keys({name: doc}))
                    #dataset['training'].update({name: doc})

    with open('muc7.json', 'w') as f:
        json.dump(dataset, f)

    return dataset


if __name__=='__main__':
    data_dir = "./muc_7/data/"
    dataset = run_muc_parser(data_dir)

















