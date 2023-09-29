from promptflow import tool
import numpy as np


@tool
def concat_results(f1_score: str):
    import json

    load_list = [{'name': 'f1_score', 'score': f1_score}]
    score_list = []
    errors = []
    for item in load_list:
        try:
            score = json.loads(item["score"])
        except Exception as e:
            try:
                score = float(item["score"])
            except Exception:
                score = np.nan
            errors.append({"name": item["name"], "msg":  str(e), "data": item["score"]})
        score_list.append({"name": item["name"], "score": score})

    variant_level_result = {}
    for item in score_list:
        item_name = str(item["name"])
        variant_level_result[item_name] = item["score"]
    return variant_level_result
