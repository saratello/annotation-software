from typing import Dict, List, Union, Tuple
from string import punctuation as punc
from collections import namedtuple
import re
import os
import json

from git import Repo, RemoteReference

POS = str
ExampleFieldGulf = str # ['baseword', 'gloss', 'clitic', 'context']
ExampleFieldCODA = str  # ['raw', 'context']
ExampleFieldMSA = str # ['segment', 'gloss', 'context']
SegmentType = str # ['baseword', 'enclitic', 'proclitic']
ExampleGulf = Dict[ExampleFieldGulf, str]
ExampleCODA = Dict[ExampleFieldCODA, str]
ExampleMSA = Dict[ExampleFieldMSA, str]
ExamplesQueryFilter = namedtuple('ExamplesQueryFilter', 'segment_type match_type resource')

ARABIC_LETTERS = "ءؤئابتثجحخدذرزسشصضطظعغفقكلمنهوىي"

def search_bar_examples(query: str,
                        gulf_tag_examples: Dict[SegmentType, Dict[POS, List[ExampleGulf]]],
                        coda_examples: List[Tuple[str]],
                        query_filter: Tuple[str] = ('Baseword', 'Approximate', 'Gulf Tags')
                        ) -> Union[Dict[POS, List[ExampleGulf]], List[ExampleCODA], Dict[POS, List[ExampleMSA]]]:
    """Function which allows to search for specific examples in a static JSON file using a filter.
    For the query filter:
        - In index 0, possible choices are 'Baseword', 'Enclitic', 'Proclitic'.
        - In index 1, possible choices are 'Approximate', 'Exact' (whether the match should be exact or not).
        - In index 2, possible choices are 'Gulf Tags', 'MSA Tags', 'CODA Examples'.

    Args:
        query (str): what the user will type in the search bar.
        gulf_tag_examples (Dict[SegmentType, Dict[POS, List[Dict[ExampleField, str]]]]): already parsed static JSON object sitting in memory
        query_filter (Optional[List[str]], optional): Should be drop down menus where the user specifies what he is searching for. Defaults to ('Baseword', 'Approximate', 'Gulf Tags').

    Returns:
        Union[Dict[POS, List[Union[ExampleGulf, ExampleMSA]]], List[ExampleCODA]]: Dictionary with a structure which depends on the value chosen for the resource type (index 2) in the query filter
    """
    query_filter = ExamplesQueryFilter(*query_filter)
    
    if 'Tags' in query_filter.resource:
        response: Dict[POS, List[Union[ExampleGulf, ExampleMSA]]] = {}

        is_pos = True if query.translate(
            str.maketrans('', '', punc)).isupper() else False
        is_arabic_str = True if query[0] in ARABIC_LETTERS else False
        is_gloss = True if [True for char in query if char.islower(
        ) and char not in ARABIC_LETTERS] else False

        gulf_tag_examples: Dict[POS, List[ExampleGulf]] = gulf_tag_examples[query_filter.segment_type.lower()]

        if is_pos:
            for k, v in gulf_tag_examples.items():
                if query_filter.match_type == 'Approximate':
                    if query in k:
                        response[k] = v
                elif query_filter.match_type == 'Exact':
                    if query == k:
                        response[k] = v

        elif is_arabic_str or is_gloss:
            example_key = 'baseword' if query_filter.segment_type.lower() == 'baseword' else 'clitic'
            example_key = 'gloss' if is_gloss else example_key
            for k, v in gulf_tag_examples.items():
                v_: List[ExampleGulf] = []
                for example in v:
                    if query_filter.match_type == 'Approximate':
                        if query in example[example_key]:
                            v_.append(example)
                    elif query_filter.match_type == 'Exact':
                        if query == example[example_key]:
                            v_.append(example)
                response.setdefault(k, []).append(v_)
    
    elif query_filter.resource == 'CODA Examples':
        response: List[ExampleCODA] = []
        for example in coda_examples:
            if query_filter.match_type == 'Approximate':
                if query in example['raw'] or query in example['coda']:
                    response.append(example)
            elif query_filter.match_type == 'Exact':
                if query == example['raw'] or query == example['coda']:
                    response.append(example)
    
    return response

Annotator = str
Feature = str # ['raw', 'coda', 'segments']
AnnotationField = str  # ['text', 'verb_form', 'pos', 'lemma']
Segment = Dict[AnnotationField, str]
Annotation = Dict[Feature, Union[str, List[str], List[Segment]]]
FilteredAnnotation = namedtuple('FilteredAnnotation', 'annotator id annotation')
AnnotationsQueryFilter = namedtuple('AnnotationsQueryFilter', 'feature field match annotators')

# Probably not the final list
ANNOTATORS = ['Christian', 'Jana', 'Wiaam', 'Sarah', 'Carine']

def search_bar_previous_annotations(query: str,
                                    annotations_json: Dict[Annotator, List[Annotation]],
                                    query_filter: Tuple[str] = ('Raw', 'Text', 'Approximate', 'Christian')
                                    ) -> List[Annotation]:
    """Function which allows to search for previously done annotations the contents of which match the values of the filter.
    For the query filter:
        - In index 0, possible choices are 'Raw', 'CODA', 'Segments'.
        - In index 1, possible choices are 'Text', 'Verb Form', 'POS', 'Lemma'.
        - In index 2, possible choices are 'Approximate', 'Exact' (whether the match should be exact or not).
        - In index 3, possible choices are the names of the annotators, to be defined in a separate list.

    Args:
        query (str): what the user will type in the search bar.
        annotations_json (Dict[Annotator, List[Annotation]]): JSON file containing the already finished annotations
        query_filter (Tuple[str], optional): Should be dropdown menus where the user specifies what he is searching for. Defaults to ('Raw', 'Text', 'Approximate', 'Christian').

    Returns:
        List[Annotation]: List of annotations to show that we can scroll through.
    """
    query_filter = AnnotationsQueryFilter(*query_filter)

    # Filtering by annotator
    annotators = ANNOTATORS
    annotators = [query_filter.annotators] if query_filter.annotators in ANNOTATORS else ANNOTATORS
    if query_filter.annotators in [f'All But {annotator}' for annotator in ANNOTATORS]:
        annotators.remove(re.sub('All But ', '', query_filter.annotators))
    
    # Filtering by feature
    annotations_filtered: List[FilteredAnnotation] = []
    for annotator, annotations in annotations_json.items():
        if annotator in annotators:
            for i, annotation in enumerate(annotations):
                if query_filter.feature.lower() == 'segments':
                    for token in annotation[query_filter.feature.lower()]:
                        for segment in token:
                            annotations_filtered.append(FilteredAnnotation(
                                annotator, i, segment[query_filter.field.lower()]))
                else:
                    annotations_filtered.append(FilteredAnnotation(
                        annotator, i, annotation['_'.join(query_filter.feature.lower().split())]))

    already_added = []
    response: List[Annotation] = []
    for annotation in annotations_filtered:
        if query_filter.match.lower() == 'approximate':
            if query in annotation.annotation and \
                (annotation.annotator, annotation.id) not in already_added:
                response.append(
                    annotations_json[annotation.annotator][annotation.id])
        elif query_filter.match.lower() == 'exact':
            if query == annotation.annotation and \
                (annotation.annotator, annotation.id) not in already_added:
                response.append(
                    annotations_json[annotation.annotator][annotation.id])

    return response


COMMIT_MESSAGE = 'No message'

def clone_repo(repo_dir='/Users/chriscay/thesis/annotation_wiaam',
               username='christios',
               password='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',
               repo_name='annotation',
               annotator_name='Wiaam') -> None:
    """This method is called once, when the annotator sets up their local application.
    What it does:
        - Clones a remote repository that I have already set up
        - Sets up a local branch in the annotator's name and its corresponding up-stream branch
    """
    repo_url = f"https://{username}:{password}@github.com/{username}/{repo_name}.git"
    repo = Repo.clone_from(repo_url, repo_dir)
    origin = repo.remote('origin')
    current = repo.create_head(annotator_name)
    current.checkout()
    origin.push(annotator_name)
    # Create up-stream branch
    repo.head.reference = repo.create_head(annotator_name)
    rem_ref = RemoteReference(repo, f"refs/remotes/origin/{annotator_name}")
    repo.head.reference.set_tracking_branch(rem_ref)


def sync_annotations(repo_dir='/Users/chriscay/thesis/annotation',
                     annotator_name='Christian') -> None:
    """This method is called each time the annotator presses the `Sync` button.
    What it does:
        - Checks out the branch in the annotator's name
        - Commits the contents of the working directory
        - Pushes the commit to the remote branch in the annotator's name
        - Checks out local main
        - Locally merges all the remote branches (one for each annotator) into local main
        - Checks out the branch in the annotator's name again
    """
    repo = Repo(repo_dir)
    repo.git.checkout(annotator_name)
    annotator_file_path = f'{annotator_name}.json'
    open(os.path.join(repo_dir, annotator_file_path), 'w').close()
    repo.index.add([annotator_file_path])
    repo.index.commit(COMMIT_MESSAGE)
    repo.git.push('origin', annotator_name)

    repo.git.fetch()
    remote_branches = repo.git.branch('-r').splitlines()
    remote_branches = [branch.strip()
                       for branch in remote_branches if re.match(r'\w+/\w+$', branch.strip(), re.M) and 'main' not in branch]
    repo.git.checkout('main')
    for branch in remote_branches:
        repo.git.merge(branch.strip())
    repo.git.checkout(annotator_name)


def get_merged_json(repo_dir='/Users/chriscay/thesis/annotation',
                    annotator_name='Christian') -> Dict[Annotator, List[Annotation]]:
    """This method should be called to get the JSON file with the annotator's respective
    annotations. This is the file which should be edited by the platform in the working 
    directory.
    """
    repo = Repo(repo_dir)
    repo.git.checkout('main')
    annotator_file_paths = [file_path for file_path in os.listdir(repo_dir) if '.json' in file_path]
    annotations_json: Dict[Annotator, List[Annotation]] = {}
    for annotator_file_path in annotator_file_paths:
        with open(os.path.join(repo_dir, annotator_file_path)) as f:
            try:
                annotations_json[annotator_file_path.strip(
                    '.json')] = json.load(f)
            except json.JSONDecodeError:
                annotations_json[annotator_file_path.strip(
                    '.json')] = []
    repo.git.checkout(annotator_name)
    return annotations_json


# with open('/Users/chriscay/thesis/pos_examples.json') as f:
#     gulf_tag_examples = json.load(f)

# with open('/Users/chriscay/thesis/coda_examples.json') as f:
#     coda_examples = json.load(f)

# with open('/Users/chriscay/Library/Containers/com.apple.mail/Data/Library/Mail Downloads/6A3F79B7-E791-498F-87DD-A0238023A21E/data.json') as f:
#     annotations_json = json.load(f)

# search_bar_previous_annotations('p1', annotations_json, ('Segments', 'POS', 'Approximate', 'Christian'))
# search_bar_examples('ليش', gulf_tag_examples, coda_examples, ('Enclitic', 'Approximate', 'CODA Examples'))


# clone_repo(repo_dir='/Users/chriscay/thesis/annotation_carine',
#            annotator_name='Carine')
# sync_annotations(repo_dir='/Users/chriscay/thesis/annotation_wiaam',
#                     annotator_name='Wiaam')
# get_merged_json(repo_dir='/Users/chriscay/thesis/annotation_wiaam',
#                 annotator_name='Wiaam')
