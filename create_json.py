import re
import json
import os 
SPEAKER_INDENT = 37
DIALOGUE_INDENT = 25 
entry = 1
filename = 'dialogue.json'

def check_line(line):
    match = re.match(r'^\s*', line)
    leading_spaces = len(match.group(0)) if match else 0
    if leading_spaces == 37 and line.strip != '' :
        return 'speaker'
    elif leading_spaces == 25 and line.strip != '':
        return 'dialogue'
    else:
        return 'something'
        
def append_to_json(speaker, dialogue):
    global entry
    data = []

    # Try loading existing JSON
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print(f"Warning: {filename} contains invalid JSON. Starting fresh.")
            data = []

    # Only append if speaker is valid (not None or empty string)
    if speaker:
        new_entry = {
            "speaker": speaker,
            "dialogue": dialogue,
            "line_number": entry
        }
        data.append(new_entry)

        print('Entry', entry)
        entry = entry + 1

    # Save updated data
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)
        


def parse_screenplay(script_text):
    i = 0
    dialogues = []
    current_speaker = None
    current_dialogue_lines = []
    print(len(script_text))
    lines = script_text.split('\n')
    print('Number of lines', len(lines))
    while(i < len(lines)):
        print('outerloop',i)  
        dialogues = ''
        current_speaker = None
        if check_line(lines[i]) == 'speaker':
            current_speaker = lines[i].strip()
            i=i+1
            while(  i < len(lines) and check_line(lines[i]) != 'speaker'):
                print('innerloop',i)
                if(check_line(lines[i])=='dialogue'):
                    dialogue = lines[i].strip()
                    dialogues = dialogues + ' ' + dialogue
                    i+=1
                else:
                    i+=1
            append_to_json(current_speaker, dialogues)
        else:
            i=i+1
       
                    

def check_type(script_text):
    lines = script_text.split('\n')
    i = 0
    while( i < 39):
        print(f'{check_line(lines[i])} line number{i + 1}')
        i+=1

def parse():
    with open("poc_test.txt", "r", encoding="latin1") as file:
        content = file.read()
    parse_screenplay(content)
if __name__ == "__main__":
    parse()