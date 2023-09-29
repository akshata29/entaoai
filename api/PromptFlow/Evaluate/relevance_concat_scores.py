from promptflow import tool
import numpy as np
import re


@tool
def concat_results(relevance_score: str):

    load_list = [{'name': 'gpt_relevance', 'score': relevance_score}]
    score_list = []
    errors = []
    for item in load_list:
        try:
            score = item["score"]
            match = re.search(r'\d', score)
            if match:
                score = match.group()
            score = float(score)
        except Exception as e:
            score = np.nan
            errors.append({"name": item["name"], "msg":   str(e), "data": item["score"]})
        score_list.append({"name": item["name"], "score": score})

    variant_level_result = {}
    for item in score_list:
        item_name = str(item["name"])
        variant_level_result[item_name] = item["score"]
        variant_level_result[item_name + '_pass_rate'] = 1 if item["score"] > 3 else 0
    return variant_level_result
