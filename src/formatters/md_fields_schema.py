import textwrap


def db_fields_schema_to_md(schema):
    rows = []
    for section_id, section_rows in schema.items():
        section_title = {
            'main': None,
            'statistics': 'Statistics fields',
            'auxiliary': 'Auxiliary fields',
        }[section_id]
        if section_title:
            rows.append(f'    <td colspan="4" align="center"><b>{section_title}</b></td>\n')

        for row in section_rows:
            field_id = row['field']
            field_type = row['type']
            if field_type.startswith('unsigned_'):
                field_type = field_type.replace('unsigned_', '')
            field_example = row.get('example')
            field_descr = row['description']

            if field_type == 'ipfs':
                field_example = field_example or 'Qma11k...'
                field_type = 'string'

            elif field_type == 'boolean':
                field_example = '1</code> <code>0'

            elif field_type == 'address':
                field_example = field_example or 'tz1UBZUk...'
                field_type = 'string'

            elif field_type == 'event':
                field_id = '</code><br><code>'.join([
                    f'{field_id}{postfix}'
                    for postfix in [
                        '_iso_date',
                        '_stamp',
                        '_hash',
                        '_row_id',
                    ]
                ])
                field_example = field_example or '</code><br><code>'.join([
                    '"2021-03-01T15:00:03Z"',
                    '1614610803',
                    '"oom5Ju6X9nYpBCi..."',
                    '42181049',
                ])
                field_type = '</code><br><code>'.join([
                    'string',
                    'integer',
                    'string',
                    'integer',
                ])

            elif field_type == 'float_set':
                field_id_stem = '_'.join(field_id.split('_')[:-1])
                field_id = '</code><br><code>'.join([
                    f'{field_id_stem}_count',
                    f'{field_id_stem}_nonzero_count',
                    f'{field_id_stem}_zero_count',
                    f'{field_id}_min',
                    f'{field_id}_max',
                    f'{field_id}_sum',
                    f'{field_id}_avg',
                ])
                field_example = field_example or '</code><br><code>'.join([
                    '100',
                    '10',
                    '1.25',
                    '2.5',
                    '33.7',
                    '1.325',
                ])
                field_type = '</code><br><code>'.join([
                    'integer',
                    'integer',
                    'float',
                    'float',
                    'float',
                    'float',
                ])

            if field_type == 'string':
                if not field_example or '<code>' not in field_example:
                    field_example = f'"{field_example}"'

            row_md = ''
            row_md += f'<td><code>{field_id}</code></td>\n'
            row_md += f'<td><code>{field_type}</code></td>\n'
            row_md += f'<td><code>{field_example}</code></td>\n'
            row_md += f'<td>{field_descr}</td>\n'
            rows.append(textwrap.indent(row_md, '    '))

    rows = '</tr><tr>\n'.join(rows)
    return textwrap.dedent('''
        <table><tr>
            <th>field</th>
            <th>type</th>
            <th>example</th>
            <th>description</th>
        </tr><tr>
    ''').strip() + rows + '</tr></table>'
