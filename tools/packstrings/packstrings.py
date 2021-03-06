#!/usr/bin/env python3

import argparse
import csv

parser = argparse.ArgumentParser(
    description='Pack Bus Pirate strings into something that can be '
                'included by the firmware.')
parser.add_argument('source', metavar='TEXT',
                    type=argparse.FileType('r'), help='the string file')
parser.add_argument('outbase', metavar='OUTPUT', type=str,
                    help='the base filename for output files')
parser.add_argument('guard', metavar='GUARD', type=str,
                    help='an additional marker to put in the C header '
                         '#include guard block')

lines = []

args = parser.parse_args()
for row in csv.reader(args.source, delimiter='\t', quotechar='\\',
                      dialect='unix'):
    if len(row) != 3:
        continue
    if row[0].strip().startswith('//'):
        continue
    if row[1] not in ('0', '1'):
        continue
    row[2] = row[2].strip()
    if not (row[2].startswith('"') and row[2].endswith('"')):
        continue
    row[2] = row[2][1:-1].replace('\\r', '\r').replace('\\n', '\n').replace(
        '\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')

    lines.append(row)

with open(args.outbase + '.s', 'w') as assembly_output:
    assembly_output.write('.global _bp_messages\n\n')
    assembly_output.write('_bp_messages:\n\n')

    for row in sorted(lines):
        assembly_output.write('\t; %s\n' % row[0])
        data = row[2].replace('\\', '\\\\').replace('\n', '\\n').replace(
            '\r', '\\r').replace('"', '\\"').replace('\t', '\\t')
        assembly_output.write('\t.pascii "%s"\n\n' % data)

offset = 0
BUFFER_WRITE_CALL = 'bp_message_write_buffer'
LINE_WRITE_CALL = 'bp_message_write_line'

with open(args.outbase + '.h', 'w') as header_output:
    header_output.write('#ifndef BP_MESSAGES_%s_H\n' % args.guard.upper())
    header_output.write('#define BP_MESSAGES_%s_H\n\n' % args.guard.upper())

    for row in sorted(lines):
        call = BUFFER_WRITE_CALL if row[1] == '0' else LINE_WRITE_CALL
        header_output.write('#define %s %s(%d, %d)\n' %
                            (row[0], call, offset, len(row[2])))
        offset += len(row[2])

    header_output.write('\n#endif /* BP_MESSAGES_%s_H */\n' %
                        args.guard.upper())

# vim:sts=2:sw=2:ts=2:et:syn=python:fdm=marker:ff=unix:fenc=utf-8:number:cc=80
