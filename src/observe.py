from __future__ import annotations
import json, os
from datetime import date
from pathlib import Path
from google import genai
from google.genai import types
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config.json').read_text())

def main():
    today=date.today(); launch=date.fromisoformat(CFG['launch_date']); day=(today-launch).days+1
    if day<1: print('H41 has not launched yet.'); return
    if day>CFG['total_days']: print('H41 mission complete.'); return
    out=ROOT/'observations'/f'{day:03d}.md'
    if out.exists(): print(f'Observation {day} already exists.'); return
    prev='First contact.'
    if day>1:
        p=ROOT/'observations'/f'{day-1:03d}.md'
        if p.exists(): prev=p.read_text()[-12000:]
    memory=(ROOT/'state/memory.md').read_text()[-12000:]
    foundation=(ROOT/'prompts/foundation.md').read_text()
    mode='present' if day%2 else 'past'; remaining=CFG['total_days']-day
    task=f'''{foundation}\n\nCURRENT CONDITIONS\nDate: {today.isoformat()}\nObservation: {day}/{CFG["total_days"]}\nObservations remaining after today: {remaining}\nMode today: {mode.upper()}\n\nPRIVATE WORKING MEMORY\n{memory}\n\nYESTERDAY\n{prev}\n\nTODAY'S TASK\n'''
    task += ('Observe something occurring in or revealing about the human world now. Use Google Search when useful. Carry yesterday into what you choose to notice.' if mode=='present' else 'Travel into the human past because of a thread from yesterday. Use Google Search to ground factual claims. Do not choose an analogy merely because it is convenient.')
    client=genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    resp=client.models.generate_content(model=CFG['model'],contents=task,config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())],response_mime_type='application/json'))
    data=json.loads(resp.text)
    md=f'''---\nday: {day}\ndate: {today.isoformat()}\nmode: {mode}\ntitle: {json.dumps(data["title"])}\n---\n\n# {data["title"]}\n\n{data["observation"].strip()}\n\n---\n\n**Thread carried:** {data.get("thread_carried","")}\n\n**Question left open:** {data.get("open_question","")}\n'''
    out.write_text(md)
    state=json.loads((ROOT/'state/state.json').read_text()); state['last_day']=day; state['last_date']=today.isoformat()
    for u in data.get('belief_updates',[]): state.setdefault('beliefs',[]).append({'day':day,**u})
    (ROOT/'state/state.json').write_text(json.dumps(state,indent=2,ensure_ascii=False))
    with (ROOT/'state/memory.md').open('a') as f: f.write(f'\n## Day {day}\n{data.get("memory_note","")}\nOpen question: {data.get("open_question","")}\n')
    print(f'Created observation {day}')
if __name__=='__main__': main()
