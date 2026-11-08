#!/usr/bin/env python3
"""Interactive TopstepX data connection; credentials stay in process memory."""
import getpass,json,os
from pathlib import Path
from app import Runtime,serve
from projectx import ProjectX
from types import SimpleNamespace

def main():
    print('TOPSTEPX DATA → LOCAL PAPER BROKER. No Topstep account orders will be sent.')
    os.environ['PROJECTX_USERNAME']=input('TopstepX username: ').strip()
    os.environ['PROJECTX_API_KEY']=getpass.getpass('API key (hidden): ').strip()
    c=json.loads((Path(__file__).parent/'config.json').read_text())
    client=ProjectX();contracts=client.contracts(c['symbol'])
    if not contracts:raise RuntimeError('No contracts returned; check market data subscription')
    for i,x in enumerate(contracts):
        print(f"{i}: {x['name']} | {x.get('description','')} | active={x.get('activeContract')} | tick={x.get('tickSize')} | tick $={x.get('tickValue')}")
    idx=int(input('Select the intended contract number: '))
    if idx<0 or idx>=len(contracts):raise ValueError('Contract number out of range')
    contract=contracts[idx]
    c.update(symbol=contract['name'],tick_size=float(contract['tickSize']),tick_value=float(contract['tickValue']))
    args=SimpleNamespace(mode='projectx',contract=contract['id'],csv=None)
    r=Runtime(args,c);r.client=client
    print('Open http://127.0.0.1:8765 and click Start. First poll warms indicators only.')
    try:serve(r,8765)
    except KeyboardInterrupt:
        with r.lock:r.persist();r.db.close()
        print('\nStopped. Restart begins a new local paper run.')
if __name__=='__main__':
    try:main()
    except Exception as exc:print(f'Connection failed: {exc}');raise SystemExit(1)
