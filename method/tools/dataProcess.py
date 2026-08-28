import json


def format_converse(file_path):
    var_set = []
    var_explanation = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for row in data:
                for var in row['influence_factor']:
                    var_set.append(next(iter(var)))
                    var_explanation.append(var)
                for var in row['response_var']:
                    var_set.append(var.keys)
                    var_explanation.append(next(iter(var)))
    except FileNotFoundError:
        print('File not found')
    return var_set, var_explanation


if __name__ == '__main__':
    file_path = '../mapper/reqAnalysisResult.json'
    var_set, var_explanation = format_converse(file_path=file_path)
    print(len(var_set), len(var_explanation))
    print(var_set)
    print(var_explanation)