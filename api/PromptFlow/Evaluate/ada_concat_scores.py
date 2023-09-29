from promptflow import tool
import numpy as np


@tool
def concat_results(ada_cosine_similarity: str):
    import json

    load_list = [{'name': 'ada_similarity', 'score': ada_cosine_similarity}]
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
        if "gpt" in item_name:
            variant_level_result[item_name + '_pass_rate'] = 1 if item["score"] >= 3 else 0
    return variant_level_result
