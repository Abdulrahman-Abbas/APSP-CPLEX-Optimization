"""Beginner-friendly dataset inspector. Needs only Python standard library."""
from pathlib import Path
import xml.etree.ElementTree as ET
import argparse

def inspect(file: Path):
    root = ET.parse(file).getroot()
    print(f"\nFILE: {file.name}")
    actors = root.findall('.//sdf/actor')
    channels = root.findall('.//sdf/channel')
    processors = root.findall('.//processor')
    print(f"Tasks (actors): {len(actors)}")
    print(f"Dependencies (channels): {len(channels)}")
    print(f"Processor entries: {len(processors)}")
    print('\nFirst five tasks:')
    for a in actors[:5]:
        print(' ', a.attrib.get('name'), 'ports=', len(a.findall('./port')))
    print('\nFirst five precedence channels:')
    for c in channels[:5]:
        print(' ', c.attrib)
    print('\nExecution-time / platform excerpt:')
    for tag in root.iter():
        if tag.tag in {'processor', 'executionTime', 'actorProperties'}:
            print(' ', tag.tag, tag.attrib, (tag.text or '').strip()[:70])
            if tag.tag == 'executionTime':
                break

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--graph',default='graph__10-1000-0.10-02_0.xml')
    a=p.parse_args()
    inspect(Path(__file__).resolve().parent/'benchmark'/'graphs'/a.graph)
