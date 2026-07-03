#!/usr/bin/env python3
import asyncio, os
from pathlib import Path
from google import genai
from google.genai import types

ROOT=Path('/Users/xlzj/Desktop/Seedance真人视频-美业活动')
OUT=ROOT/'02-生成产出/output_gemini_omni_test'
OUT.mkdir(parents=True, exist_ok=True)

async def main():
    api_key=os.environ.get('GEMINI_API_KEY')
    if not api_key: raise SystemExit('Missing GEMINI_API_KEY')
    client=genai.Client(http_options={'api_version':'v1beta'}, api_key=api_key)
    config=types.LiveConnectConfig(
        response_modalities=[types.Modality.IMAGE],
        system_instruction='You are a visual generation model. Return image output only if supported.'
    )
    async with client.aio.live.connect(model='models/gemini-omni-flash-preview', config=config) as session:
        await session.send_client_content(turns={
            'role':'user',
            'parts':[{'text':'Generate one vertical beauty campaign image of an adult woman in a blue-white gingham ruffle outfit standing in a pink floral beauty event background. No text.'}]
        }, turn_complete=True)
        idx=0
        async for msg in session.receive():
            print('message', msg.model_dump(exclude_none=True).keys())
            sc=msg.server_content
            if sc and sc.model_turn and sc.model_turn.parts:
                for part in sc.model_turn.parts:
                    print('part', part.model_dump(exclude_none=True).keys())
                    if part.inline_data and part.inline_data.data:
                        mime=part.inline_data.mime_type or 'application/octet-stream'
                        ext='png' if 'png' in mime else 'jpg' if 'jpeg' in mime else 'bin'
                        out=OUT/f'omni_image_{idx:02d}.{ext}'
                        out.write_bytes(part.inline_data.data)
                        print('saved', out, mime, len(part.inline_data.data))
                        idx+=1
                    if part.text:
                        print('text', part.text[:500])
            if sc and sc.turn_complete:
                break
    print('done')

asyncio.run(main())
