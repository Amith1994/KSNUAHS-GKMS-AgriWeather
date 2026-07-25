import json

with open('data_embedded.json', 'r') as f:
    raw_data = json.load(f)

json_districts = json.dumps(raw_data['districts'])
json_taluks = json.dumps(raw_data['taluks'])

with open('template_rainfall_status.html', 'r', encoding='utf-8') as f:
    template = f.read()

template = template.replace('__JSON_DISTRICTS__', json_districts)
template = template.replace('__JSON_TALUKS__', json_taluks)

with open('rainfall status.html', 'w', encoding='utf-8') as f:
    f.write(template)

print('Created rainfall status.html successfully!')
