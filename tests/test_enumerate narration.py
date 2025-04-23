import json


def main(jsob: str) -> dict:
    try:
        
        jsob_dict = json.loads(jsob)
        content = jsob_dict.get('content', [])
        narrations = []
        for index, item in enumerate(content, start=1):
            
            narration = item.get('Narration', '')
            if isinstance(narration, str):
                narrations.append(f"{index}. {narration}")
        concatenated_narration = '\n\n'.join(narrations)
        return {'result': concatenated_narration}
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        return {'result': f"Error processing JSON: {str(e)}"}
    
if __name__ == "__main__":
    jsob = '''
    {
        "content": [
            {"Narration": "This is the first narration."},
            {"Narration": "This is the second narration."},
            {"Narration": "This is the third narration."}
        ]
    }
    '''
    result = main(jsob)
    print(result)